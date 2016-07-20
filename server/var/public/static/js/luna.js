/**
 * LUNA - Responsive Admin Theme
 *
 */

;(function (global) {
    'use strict';
    var ValueError = function (message) {
        var err = new Error(message);
        err.name = 'ValueError';
        return err;
    };
    var defaultTo = function (x, y) {
        return y == null ? x : y;
    };
    var create = function (transformers) {
        return function (template) {
            var args = Array.prototype.slice.call(arguments, 1);
            var idx = 0;
            var state = 'UNDEFINED';
            return template.replace(
                /([{}])\1|[{](.*?)(?:!(.+?))?[}]/g,
                function (match, literal, key, xf) {
                    if (literal != null) {
                        return literal;
                    }
                    if (key.length > 0) {
                        if (state === 'IMPLICIT') {
                            throw ValueError('cannot switch from ' +
                                'implicit to explicit numbering');
                        }
                        state = 'EXPLICIT';
                    } else {
                        if (state === 'EXPLICIT') {
                            throw ValueError('cannot switch from ' +
                                'explicit to implicit numbering');
                        }
                        state = 'IMPLICIT';
                        key = String(idx);
                        idx += 1;
                    }
                    var value = defaultTo('', lookup(args, key.split('.')));
                    if (xf == null) {
                        return value;
                    } else if (Object.prototype.hasOwnProperty.call(transformers, xf)) {
                        return transformers[xf](value);
                    } else {
                        throw ValueError('no transformer named "' + xf + '"');
                    }
                }
            );
        };
    };
    var lookup = function (obj, path) {
        if (!/^\d+$/.test(path[0])) {
            path = ['0'].concat(path);
        }
        for (var idx = 0; idx < path.length; idx += 1) {
            var key = path[idx];
            obj = typeof obj[key] === 'function' ? obj[key]() : obj[key];
        }
        return obj;
    };
    var format = create({});
    format.create = create;
    format.extend = function (prototype, transformers) {
        var $format = create(transformers);
        prototype.format = function () {
            var args = Array.prototype.slice.call(arguments);
            args.unshift(this);
            return $format.apply(global, args);
        };
    };
    if (typeof module !== 'undefined') {
        module.exports = format;
    } else if (typeof define === 'function' && define.amd) {
        define(function () {
            return format;
        });
    } else {
        global.format = format;
    }
}.call(this, this));

$(document).ready(function () {
    $('.left-nav-toggle a').on('click', function (event) {
        event.preventDefault();
        $("body").toggleClass("nav-toggle");
    });
    $('.nav-second').on('show.bs.collapse', function () {
        $('.nav-second.in').collapse('hide');
    });
    $('.panel-toggle').on('click', function (event) {
        event.preventDefault();
        var hpanel = $(event.target).closest('div.panel');
        var icon = $(event.target).closest('i');
        var body = hpanel.find('div.panel-body');
        var footer = hpanel.find('div.panel-footer');
        body.slideToggle(300);
        footer.slideToggle(200);
        icon.toggleClass('fa-chevron-up').toggleClass('fa-chevron-down');
        hpanel.toggleClass('').toggleClass('panel-collapse');
        setTimeout(function () {
            hpanel.resize();
            hpanel.find('[id^=map-]').resize();
        }, 50);
    });
    $('.panel-close').on('click', function (event) {
        event.preventDefault();
        var hpanel = $(event.target).closest('div.panel');
        hpanel.remove();
    });
});