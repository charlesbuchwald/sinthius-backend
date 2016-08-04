#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:29
# ~

import sys
import math
import toro
import datetime
from sinthius.conf import settings
from sinthius.op.context import ContextLocal
from sinthius.utils.decorators import try_or_none, try_or_dict
from sinthius.utils.filetools import import_object, gzip_decode
from sinthius.utils.logtools import trace
from sinthius.utils.regex import rx_template_name
from sinthius.utils.serializers import jsondumps, jsonloads
from sinthius.utils.strtools import camel_case_split
from sinthius import compat, constants
from sinthius.errors import ApiRequestError, ApiResponseError
from bson.json_util import dumps as mongodb_dumps
from functools import wraps
from pymongo.cursor import Cursor
from tornado import httputil, web, locale, gen

SUCCESS_CODE = 0
SUCCESS_MESSAGE = 'success'
ERROR_CODE = 1
ERROR_MESSAGE = 'error'
NOT_FOUND = 404
NOT_IMPLEMENTED_CODE = 404


def is_trackable(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not getattr(self, 'track', False):
            return None
        return method(self, *args, **kwargs)
    return wrapper


def is_finished(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if getattr(self, '_finished', False):
            return None
        return method(self, *args, **kwargs)
    return wrapper


class Paginator(object):
    def __init__(self, page_number=0, page_size=50, total=0, query=None):
        self._page_number = page_number
        self._page_size = page_size
        self._total = total
        self._page_query = query

    @property
    def total(self):
        return int(self._total)

    @property
    def page_total(self):
        return int(math.ceil(self.total / float(self.page_size)))

    @property
    def page_number(self):
        return int(self._page_number)

    @property
    def page_size(self):
        return int(self._page_size)

    @property
    def page_next(self):
        if self.page_number < self.page_total:
            return self.page_number + 1
        else:
            return self.page_total

    @property
    def page_prev(self):
        if self.page_number > 1:
            return self.page_number - 1
        else:
            return 1

    @property
    def page_query(self):
        return self._page_query

    def to_object(self):
        return {
            'total': self.total,
            'pages': self.page_total,
            'query': self.page_query,
            'page': {
                'size': self.page_size,
                'number': self.page_number,
                'next': self.page_next,
                'prev': self.page_prev,
            }
        }

    def to_json(self):
        return jsondumps(self.to_object())


class RequestContext(ContextLocal):
    def __init__(self, request):
        super(RequestContext, self).__init__()
        self.request = request
        self.user = None
        self.close_event = None


class BaseHandler(web.RequestHandler):
    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request, **kwargs)
        self._close_event = toro.Event()

    # events

    def on_connection_close(self):
        self._close_event.set()

    # datetime

    def now(self, time_zone=None):
        return datetime.datetime.now(time_zone)

    def now_delta(self, time_zone=None, **kwargs):
        return self.now(time_zone) + datetime.timedelta(**kwargs)

    def epoch(self):
        return int(datetime.datetime.now().strftime('%s'))

    def utc_now(self):
        return datetime.datetime.utcnow()

    def utc_now_delta(self, **kwargs):
        return self.utc_now() + datetime.timedelta(**kwargs)

    def utc_epoch(self):
        return int(datetime.datetime.utc_now().strftime('%s'))

    # methods

    def head(self, *args, **kwargs):
        self._not_implemented()

    def get(self, *args, **kwargs):
        self._not_implemented()

    def post(self, *args, **kwargs):
        self._not_implemented()

    def delete(self, *args, **kwargs):
        self._not_implemented()

    def patch(self, *args, **kwargs):
        self._not_implemented()

    def put(self, *args, **kwargs):
        self._not_implemented()

    def options(self, *args, **kwargs):
        self._not_implemented()

    # default

    def _not_implemented(self):
        raise web.HTTPError(NOT_IMPLEMENTED_CODE)

    @is_finished
    def default_response(self, chunk):
        self.plain_text_response(chunk)

    @is_finished
    def plain_text_response(self, chunk):
        self.set_header('Content-Type', 'text/plain; charset=UTF-8')
        self.finish(chunk)

    @is_finished
    def json_response(self, chunk, **kwargs):
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.finish(self.json_sanitizer(chunk, **kwargs))

    def json_sanitizer(self, value, **kwargs):
        if isinstance(value, compat.iter_type):
            value = self.json_dumps(value, **kwargs)
        if not isinstance(value, (compat.string_type, compat.none_type)):
            raise TypeError('Json data must be a string.')
        return value.replace("</", "<\\/")

    def json_loads(self, value, **kwargs):
        return jsonloads(value, **kwargs)

    def json_dumps(self, value, **kwargs):
        if not compat.ujson_available:
            kwargs.setdefault('separators', (',', ':'))
        return jsondumps(value, **kwargs)

    @property
    def debug(self):
        return self.application.debug

    @property
    def track(self):
        try:
            return self.settings.get('track', settings.TRACK)
        except:
            return False

    @property
    def local_domain(self):
        try:
            return self.domains['local']['domain']
        except:
            return constants.LOCALHOST

    @property
    def remote_domain(self):
        try:
            return self.domains\
                .get('remote', {})\
                .get('domain', settings.DOMAIN)
        except:
            return constants.LOCALHOST

    @property
    def short_domain(self):
        try:
            return self.domains\
                .get('short', {})\
                .get('domain', settings.DOMAIN)
        except:
            return constants.LOCALHOST

    @property
    def domains(self):
        try:
            return self.settings.get('domains', settings.DOMAINS)
        except:
            return {}

    def domain_normalizer(self, domain, port=None, protocol=None):
        domain = domain.lower()
        if domain in ('local', 'remote', 'short'):
            domain = getattr(self, '%s_domain' % domain)
        if isinstance(port, int) and -1 < port < 65536:
            domain = '%s:%s' % (domain, port)
        if isinstance(protocol, compat.string_type):
            domain = "%s://%s" % (protocol, domain)
        return domain.lower()

    @property
    def remote_ip(self):
        try:
            ip = self.request.headers.get('X-Real-Ip', self.request.remote_ip)
        except:
            ip = self.request.remote_ip
        return self.request.headers.get('X-Forwarded-For', ip)

    @property
    def root_url(self):
        try:
            return self.settings.get('root_url', settings.ROOT_URL)
        except:
            return '/'

    @property
    def login_url(self):
        try:
            return self.settings.get('login_url', settings.LOGIN_URL)
        except:
            return self.root_url

    @property
    def logout_url(self):
        try:
            return self.settings.get('logout_url', settings.LOGOUT_URL)
        except:
            return self.root_url

    @property
    def next_url(self):
        alternative = self.get_argument('next_url', self.root_url)
        return self.get_argument('next', alternative)

    def goto_root(self):
        self.redirect(self.root_url)

    def goto_next(self):
        self.redirect(self.next_url)

    def _paths(self, value=None):
        try:
            value = value.lower()
            paths = self.settings.get('paths', settings.PATHS)
            if value is None:
                return paths
            return paths[value]
        except:
            return None

    def _import_class(self, value):
        return import_object(value)

    # paginator

    def paginate(self, page_number=0, page_size=50, total=0):
        return Paginator(page_number, self.paginate_size(page_size), total)

    def paginate_size(self, size=50, max_size=200):
        size, max_size = int(size), int(max_size)
        return size if size < max_size else max_size

    # template

    _template = None

    @property
    def template(self):
        if not self._template:
            name = rx_template_name.sub('', self.__class__.__name__)
            self._template = '{1}.html'.format(*camel_case_split(name, '_'))
        return self._template

    def render(self, template_name=None, **kwargs):
        if not template_name:
            template_name = self.template
        kwargs.setdefault('scope', self)
        super(BaseHandler, self).render(template_name, **kwargs)

    # xsrf

    _check_xsrf = True

    def check_xsrf_cookie(self):
        if self._check_xsrf:
            super(BaseHandler, self).check_xsrf_cookie()

    # etag

    _check_etag = True

    def check_etag_header(self):
        if self._check_etag:
            super(BaseHandler, self).check_etag_header()

    # cookie

    def set_cookie(self, name, value, domain=None, expires=None, path="/",
                   expires_days=None, **kwargs):
        kwargs.setdefault('secure', True)
        kwargs.setdefault('httponly', True)
        if expires_days is not None and not expires:
            kwargs.setdefault(
                'max_age', expires_days * constants.SECONDS_PER_DAY)
        domain = '.%s' % self.remote_domain
        super(BaseHandler, self).set_cookie(
            name, value, domain, expires, path, expires_days, **kwargs)

    def clear_cookie(self, name, path="/", domain=None):
        domain = '.%s' % self.remote_domain
        super(BaseHandler, self).clear_cookie(name, path, domain)

    # current user

    @property
    @try_or_none
    def current_user_id(self):
        return self.current_user['id']

    @property
    @try_or_none
    def current_user_name(self):
        return self.current_user.get(
            'username', self.current_user.get('email', None))

    @property
    @try_or_none
    def current_user_locale(self):
        try:
            return self.current_user.get(
                'lang', self.current_user.get(
                    'locale', self.settings.get('locale', settings.LOCALE)))
        except:
            return constants.LOCALE

    def get_user_locale(self):
        try:
            return locale.Locale.get_closest(self.current_user_locale)
        except:
            return self.get_browser_locale(constants.LOCALE)


class APIHandler(BaseHandler):
    # TODO(berna): I need to integrate this handler with the message schema.-
    _methods_allow = ()

    def _not_implemented(self, code=NOT_IMPLEMENTED_CODE, message=None):
        if code == 405:
            self.set_header('Allow', ', '.join(self._methods_allow))
        self.normalize_response(code, message)

    def _unsupported_media_type(self):
        self.normalize_response(415)

    _json_forcing_normalization = False

    @is_finished
    def string_response(self, chunk):
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.finish(chunk)

    @is_finished
    def default_response(self, chunk, **kwargs):
        self.complex_response(chunk, **kwargs)

    @is_finished
    def complex_response(self, chunk, code=None, message=None, normalize=False,
                         **kwargs):
        try:
            normalize = normalize or self._json_forcing_normalization
            if isinstance(chunk, Exception):
                trace([self.request, self.request.arguments])
                code = getattr(chunk, 'code', code) or ERROR_CODE
                message = getattr(chunk, 'message', compat.binary_type(chunk))\
                    or message or ERROR_MESSAGE
                normalize = True
                chunk = None
            elif isinstance(chunk, Cursor):
                chunk = mongodb_dumps(chunk)
                normalize, chunk = \
                    self.json_string_normalizer(normalize, code, message, chunk)
            elif hasattr(chunk, 'to_json'):
                chunk = getattr(chunk, 'to_json')()
                normalize, chunk = \
                    self.json_string_normalizer(normalize, code, message, chunk)
            elif not isinstance(chunk, compat.string_type):
                for func in constants.PRIMITIVE_METHODS:
                    if hasattr(chunk, func):
                        chunk = getattr(chunk, func)()
                        break
            if not normalize:
                return self.json_response(chunk, **kwargs)
            self.normalize_response(code, message, chunk, **kwargs)
        except Exception, e:
            error = ApiResponseError(e.message)
            self.complex_response(error)

    @is_finished
    def normalize_response(self, code=None, message=None, response=None,
                           **kwargs):
        chunk = self.json_normalizer(code, message, response)
        self.json_response(chunk, **kwargs)

    def json_normalizer(self, code=None, message=None, response=None):
        chunk = {}
        if code in httputil.responses:
            message = httputil.responses[code]
            self.set_status(code)
        if message is not None:
            chunk['error'] = {'message': message}
            if code is not None:
                chunk['error']['code'] = code
        if response is not None:
            chunk['response'] = response
        return chunk

    def json_string_normalizer(self, normalize, code, message, chunk):
        if normalize:
            data = self.json_normalizer(code, message, '{response}')
            if code < 300:
                chunk = compat.binary_type(data).replace("'{response}'", chunk)
            else:
                del data['response']
                chunk = compat.binary_type(data)
            normalize = False
        return normalize, chunk

    @try_or_dict
    def json_body(self):
        return self.json_request()

    @try_or_dict
    def json_request(self):
        content_type = self.request.headers.get('Content-Type', '')
        if content_type.startswith('application/json'):
            content_encoding = self.request.headers.get('Content-Encoding', '')
            if not content_encoding:
                return self.json_loads(self.request.body)
            elif content_encoding == 'gzip':
                return self.json_loads(gzip_decode(self.request.body))
        self._unsupported_media_type()

    def _handle_request_exception(self, e):
        try:
            if isinstance(e, web.Finish) or self._finished:
                if not self._finished:
                    self.finish()
                return
            self.log_exception(*sys.exc_info())
            if self.debug:
                self.complex_response(e)
                return
            if isinstance(e, web.HTTPError):
                e = ApiResponseError(e.reason, e.status_code)
            elif not isinstance(e, (ApiRequestError, ApiResponseError)):
                e = ApiResponseError(e.message, ERROR_CODE)
            self.complex_response(e)
        except:
            self.normalize_response(ERROR_CODE)


class NotFoundHandler(BaseHandler):
    def get(self, *args, **kwargs):
        self.set_status(NOT_FOUND)
        chunk = '%s - %s' % (NOT_FOUND, httputil.responses[NOT_FOUND])
        self.plain_text_response(chunk)


class APINotFoundHandler(APIHandler):
    def get(self, *args, **kwargs):
        self.normalize_response(NOT_FOUND)


class PingHandler(APIHandler):
    def get(self, *args, **kwargs):
        self.plain_text_response(settings.PING_RESPONSE)


class StatsHandler(APIHandler):
    def get(self, *args, **kwargs):
        chunk = self.json_dumps(self.application.stats(), sort_keys=True)
        self.json_response(chunk)


class ConnectorsMixin(object):
    # mongodb connector
    _db_default = None

    @property
    def database(self):
        return self.db_connector(self.db_name)

    @property
    def db_name(self):
        try:
            if self._db_default is None:
                return self.settings\
                    .get('db_default', settings.DATABABES_DEFAULT)
            return self._db_default
        except:
            return constants.DEFAULT_KEY

    def db_connector(self, name):
        pass

    # key-value connector
    _kv_default = None

    @property
    def keyvalue(self):
        return self.kv_connector(self.kv_name)

    @property
    def kv_name(self):
        try:
            if self._kv_default is None:
                return self.settings\
                    .get('kv_default', settings.KEYVALUES_DEFAULT)
            return self._kv_default
        except:
            return constants.DEFAULT_KEY

    def kv_connector(self, name):
        pass

    # object connector
    _ob_default = None

    @property
    def object(self):
        return self.ob_connector(self.ob_name)

    @property
    def ob_name(self):
        try:
            if self._ob_default is None:
                return self.settings\
                    .get('ob_default', settings.OBJECTS_DEFAULT)
            return self._ob_default
        except:
            return constants.DEFAULT_KEY

    def ob_connector(self, name):
        pass

    # auditor connector
    _au_default = None

    @property
    def auditor(self):
        return self.au_connector(self.au_name)

    @property
    def au_name(self):
        try:
            if self._au_default is None:
                return self.settings\
                    .get('au_default', settings.AUDITOR_DEFAULT)
            return self._au_default
        except:
            return constants.DEFAULT_KEY

    def au_connector(self, name):
        pass


class AuditorMixin(ConnectorsMixin):
    @property
    def audited_current_user(self):
        current_user = self.current_user
        return {} if not current_user else {
            'sid': current_user.get('sid'),
            'username': current_user.get('username'),
            'remote_ip': current_user.get('remote_ip'),
            'last_login': current_user.get('last_login'),
        }

    @is_trackable
    def get_audited_activity(self, message, activity=None, **kwargs):
        if not activity:
            activity = self.request.path
        kwargs.setdefault('host', self.request.host)
        kwargs.setdefault('remote_ip', self.remote_ip)
        current_user = self.audited_current_user
        if current_user:
            kwargs.setdefault('sid', current_user.get('sid'))
            kwargs.setdefault('username', current_user.get('username'))
        kwargs.setdefault('activity', activity)
        kwargs.setdefault('message', message)
        return kwargs

    @is_trackable
    def get_audited_error(self, message, activity=None, level='warning', **kwargs):
        kwargs = self.get_audited_activity(message, activity, **kwargs)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if exc_type and exc_value:
            kwargs.setdefault('exception', exc_type.__name__)
            kwargs.setdefault(
                'file_name', exc_traceback.tb_frame.f_code.co_filename)
            kwargs.setdefault('file_line', exc_traceback.tb_lineno)
        kwargs.setdefault('level', level)
        kwargs.setdefault('arguments', self.request.arguments)
        return kwargs

    @gen.coroutine
    def push_audited_activity(self, message, activity=None, **kwargs):
        raise NotImplementedError()

    @gen.coroutine
    def push_audited_error(self, message, activity=None, **kwargs):
        raise NotImplementedError()
