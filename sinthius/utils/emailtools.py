#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:27
# ~

import io
import sys
import rfc822
from sinthius import compat
from sinthius.errors import EmailError
from functools import wraps
from tornado import gen


def is_message(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        message = args[0]
        if not isinstance(message, Mail):
            raise gen.Return(EmailError('Invalid argument type, must be a '
                                        '"bs_services.third_party.utils'
                                        '.emails.Mail"'))
        if not (message.text or message.html):
            raise gen.Return(EmailError('No body content found in message'))
        return method(self, *args, **kwargs)
    return wrapper


class SMTPAPIHeader(object):
    def __init__(self):
        self.data = {}

    def add_to(self, to):
        if 'to' not in self.data:
            self.data['to'] = []
        self.data['to'].append(to)

    def set_tos(self, tos):
        self.data['to'] = tos

    def add_substitution(self, key, value):
        if 'sub' not in self.data:
            self.data['sub'] = {}
        if key not in self.data['sub']:
            self.data['sub'][key] = []
        self.data['sub'][key].append(value)

    def set_substitutions(self, subs):
        self.data['sub'] = subs

    def add_unique_arg(self, key, value):
        if 'unique_args' not in self.data:
            self.data['unique_args'] = {}
        self.data['unique_args'][key] = value

    def set_unique_args(self, value):
        self.data['unique_args'] = value

    def add_category(self, category):
        if 'category' not in self.data:
            self.data['category'] = []
        self.data['category'].append(category)

    def set_categories(self, category):
        self.data['category'] = category

    def add_section(self, key, section):
        if 'section' not in self.data:
            self.data['section'] = {}
        self.data['section'][key] = section

    def set_sections(self, value):
        self.data['section'] = value

    def add_filter(self, app, setting, val):
        if 'filters' not in self.data:
            self.data['filters'] = {}
        if app not in self.data['filters']:
            self.data['filters'][app] = {}
        if 'settings' not in self.data['filters'][app]:
            self.data['filters'][app]['settings'] = {}
        self.data['filters'][app]['settings'][setting] = val

    def json_string(self):
        result = {}
        for key in self.data.keys():
            if self.data[key] != [] and self.data[key] != {}:
                result[key] = self.data[key]
        return compat.json.dumps(result)


class Mail(object):
    def __init__(self, **opts):
        """
        :param to: Recipient
        :param to_name: Recipient name
        :param from_email: Sender email
        :param from_name: Sender name
        :param subject: Email title
        :param text: Email body
        :param html: Email body
        :param bcc: Recipient
        :param reply_to: Reply address
        :param date: Set date
        :param headers: Set headers
        :param files: Attachments
        :param return_path: SES property
        :return:
        """
        self.to = []
        self.to_name = []
        self.cc = []
        self.add_to(opts.get('to', []))
        self.add_to_name(opts.get('to_name', []))
        self.add_cc(opts.get('cc', []))
        self.from_email = opts.get('from_email', '')
        self.from_name = opts.get('from_name', '')
        self.subject = opts.get('subject', '')
        self.text = opts.get('text', '')
        self.html = opts.get('html', '')
        self.bcc = []
        self.add_bcc(opts.get('bcc', []))
        self.reply_to = opts.get('reply_to', '')
        self.files = opts.get('files', {})
        self.headers = opts.get('headers', '')
        self.date = opts.get('date', rfc822.formatdate())
        self.content = opts.get('content', {})
        self.smtpapi = opts.get('smtpapi', SMTPAPIHeader())

        # AWS SES
        self.return_path = opts.get('return_path', None)

    def parse_and_add(self, to):
        name, email = rfc822.parseaddr(to.replace(',', ''))
        if email:
            self.to.append(email)
        if name:
            self.add_to_name(name)

    def add_to(self, to):
        if isinstance(to, str):
            self.parse_and_add(to)
        elif sys.version_info < (3, 0) and isinstance(to, unicode):
            self.parse_and_add(to.encode('utf-8'))
        elif hasattr(to, '__iter__'):
            for email in to:
                self.add_to(email)

    def add_to_name(self, to_name):
        if isinstance(to_name, str):
            self.to_name.append(to_name)
        elif sys.version_info < (3, 0) and isinstance(to_name, unicode):
            self.to_name.append(to_name.encode('utf-8'))
        elif hasattr(to_name, '__iter__'):
            for tn in to_name:
                self.add_to_name(tn)

    def add_cc(self, cc):
        if isinstance(cc, str):
            email = rfc822.parseaddr(cc.replace(',', ''))[1]
            self.cc.append(email)
        elif sys.version_info < (3, 0) and isinstance(cc, unicode):
            email = rfc822.parseaddr(cc.replace(',', ''))[1].encode('utf-8')
            self.cc.append(email)
        elif hasattr(cc, '__iter__'):
            for email in cc:
                self.add_cc(email)

    def set_from(self, from_email):
        name, email = rfc822.parseaddr(from_email.replace(',', ''))
        if email:
            self.from_email = email
        if name:
            self.set_from_name(name)

    def set_from_name(self, from_name):
        self.from_name = from_name

    def set_subject(self, subject):
        self.subject = subject

    def set_text(self, text):
        self.text = text

    def set_html(self, html):
        self.html = html

    def add_bcc(self, bcc):
        if isinstance(bcc, str):
            email = rfc822.parseaddr(bcc.replace(',', ''))[1]
            self.bcc.append(email)
        elif sys.version_info < (3, 0) and isinstance(bcc, unicode):
            email = rfc822.parseaddr(bcc.replace(',', ''))[1].encode('utf-8')
            self.bcc.append(email)
        elif hasattr(bcc, '__iter__'):
            for email in bcc:
                self.add_bcc(email)

    def set_replyto(self, replyto):
        self.reply_to = replyto

    def add_attachment(self, name, file_):
        if sys.version_info < (3, 0) and isinstance(name, unicode):
            name = name.encode('utf-8')
        if isinstance(file_, str):
            with open(file_, 'rb') as f:
                self.files[name] = f.read()
        elif hasattr(file_, 'read'):
            self.files[name] = file_.read()

    def add_attachment_stream(self, name, string):
        if sys.version_info < (3, 0) and isinstance(name, unicode):
            name = name.encode('utf-8')
        if isinstance(string, io.BytesIO):
            self.files[name] = string.read()
        else:
            self.files[name] = string

    def add_content_id(self, cid, value):
        self.content[cid] = value

    def set_headers(self, headers):
        self.headers = headers

    def set_date(self, date):
        self.date = date

    # AWS SES methods

    def set_return_path(self, value):
        self.return_path = value

    @property
    def source(self):
        if self.from_name:
            return '%s <%s>' % (self.from_name, self.from_email)
        return self.from_email

    # SMTPAPI Wrapper methods

    def add_substitution(self, key, value):
        self.smtpapi.add_substitution(key, value)

    def set_substitutions(self, subs):
        self.smtpapi.set_substitutions(subs)

    def add_unique_arg(self, key, value):
        self.smtpapi.add_unique_arg(key, value)

    def set_unique_args(self, args):
        self.smtpapi.set_unique_args(args)

    def add_category(self, cat):
        self.smtpapi.add_category(cat)

    def set_categories(self, cats):
        self.smtpapi.set_categories(cats)

    def add_section(self, key, value):
        self.smtpapi.add_section(key, value)

    def set_sections(self, sections):
        self.smtpapi.set_sections(sections)

    def add_filter(self, filter_key, setting, value):
        self.smtpapi.add_filter(filter_key, setting, value)

    def json_string(self):
        return self.smtpapi.json_string()
