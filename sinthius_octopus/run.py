#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 13/jun/2016 12:16
# ~

# Run and Initialize
if __name__ == '__main__':

    # Imports
    import os
    from sinthius.constants import ENV_SETTINGS_MODULE

    # Global settings define
    os.environ.setdefault(ENV_SETTINGS_MODULE, 'sinthius_octopus.settings')

    # Imports
    import settings as cfg
    from tornado import options
    from sinthius.conf import global_options

    # Global options define
    ROOT_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../' * 2, 'server'))
    options.define('root_path', ROOT_PATH)
    options.define('requirements_file', False)
    options.define('nuc_name', cfg.NUC_NAME)
    options.define('nuc_ip', cfg.NUC_IP)
    options.define('nuc_port', cfg.PORT)
    options.define('nuc_mode', cfg.NUC_MODE)
    options.define('nuc_priority', cfg.NUC_PRIORITY)
    options.define('nuc_description', cfg.NUC_DESCRIPTION)
    options.define('master', cfg.MASTER)
    options.parse_command_line(final=False)

    # Imports
    from sinthius.utils.filetools import check_requirements
    from sinthius.server.base import start_server, stop_server
    from importlib import import_module
    from tornado import ioloop

    # Check requirements
    if options.options.requirements_file:
        check_requirements(options.options.requirements_file)

    # Get ioloop instance
    io_loop = ioloop.IOLoop.instance()

    # Check main class
    if not options.options.main:
        raise RuntimeError('Main module is not defined')

    # Import main class
    main = import_module(options.options.main)

    # Check run method
    if not hasattr(main, 'run'):
        raise RuntimeError('Main module does not define "run" method')

    # Finally, run platform
    main.run(start_server, stop_server)
