#!/usr/bin/env python
#
# Common configuration and logging
#
# mdeacon@zorillaeng.com
#

import argparse
import ConfigParser
from os import path, access, R_OK
import os
import sys
import time
import paramiko
import platform
import glob2
import shutil
import logging
import logging.handlers
from logging.handlers import RotatingFileHandler

def get_data_path():
    """Return the package 'data' path
    """
    path = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(path, 'data')

def get_log_path():
    """Return a path where logs go
    """
    home = path.expanduser("~")
    return os.path.join(home, '.zorilla', 'log')

def get_config_path():
    """Return a path where config files live
    """
    home = path.expanduser("~")
    return os.path.join(home, '.zorilla', 'config')

def init_config(in_defaults, section = 'Defaults'):
    """Common config initialization for all test utilities
    """
    config_filename = 'default.cfg'
    # Check for existence of config directory and create if not found
    config_path = get_config_path()
    data_path = get_data_path()
    if not os.path.exists(config_path):
        print 'Creating config path % s' % config_path
        os.makedirs(config_path)
        shutil.copyfile(os.path.join(data_path, config_filename),
                        os.path.join(config_path, config_filename))
    # Parse any conf_file specification
    # We make this parser with add_help=False so that
    # it doesn't parse -h and print help.
    conf_parser = argparse.ArgumentParser(
        description=__doc__, # printed with -h/--help
        # Don't mess with format of description
        formatter_class=argparse.RawDescriptionHelpFormatter,
        # Turn off help, so we print all options in response to -h
        add_help=False
        )
    
    # Or the user may specify another
    conf_parser.add_argument("-c", "--config", help="config file", 
                             metavar="FILE", default=config_filename)
    args, remaining_argv = conf_parser.parse_known_args()
    # args.config is now either the default or the user specified config
    # Add the config path to the name
    args.config = os.path.join(get_config_path(), args.config)
    config = ConfigParser.SafeConfigParser()
    # Remove leading space from config pathname
    args.config = args.config.strip()
    if path.isfile(args.config) and access(args.config, R_OK):
        # The file exists and can be read so grab defaults from it
        config.read([args.config])
        defaults = dict(config.items(section))
    else:
        # The file doesn't exist or can't be read so use the defaults
        print('Config file %s is missing or is not readable', args.config)
        sys.exit(0)

    # Parse rest of arguments
    # The user can override any argument configured by either the default or 
    # config file with a command line argument
    # Don't suppress add_help here so it will handle -h
    parser = argparse.ArgumentParser(
        # Inherit options from config_parser
        parents=[conf_parser])
    parser.set_defaults(**defaults)

    # All tests have these parameters
    parser.add_argument("-l", "--loglevel", help="set log level",
                        choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'])
    parser.add_argument("-r", "--report", help="report filename")

    # Caller can now add custom arguments
    return parser, remaining_argv

def init_logging(argv, args, logger):
    """Set up logging
    """
    ch = logging.StreamHandler(sys.stdout)
    # Create the report directory if it doesn't exist
    log_path = get_log_path()
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    if (not args.report or args.report.isspace()):
        # Create a file based on the executable name
        filename = os.path.splitext(os.path.basename(argv[0]))[0]
        dt = '-' + time.strftime("%d-%m-%Y-%H-%M-%S")
        args.report = filename + dt + '.txt' 
    report = os.path.join(log_path, args.report)
    fh = RotatingFileHandler(report, maxBytes=4194304, backupCount=5)
    if args.loglevel == 'DEBUG':
        formatter = logging.Formatter('%(asctime)s:%(funcName)s:%(lineno)s:'
                                      '%(message)s')
        fh.setFormatter(formatter)
    logger.addHandler(fh)
    # When logging to a file, emit the command line for reference
    logger.error('Command line:')
    s = ' '.join(argv)
    logger.error(s)
    logger.addHandler(ch)

    logger.setLevel(args.loglevel)

    # Assign log for paramiko events
    paramiko.util.log_to_file(os.path.join(log_path, 'paramiko.log'))
    logging.getLogger("paramiko").setLevel(args.loglevel)

    return args.report
