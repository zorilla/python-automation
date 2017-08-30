#!/usr/bin/env python
#
# Run GDB backtrace on user specified binary
#
#    Gather all threads
#    For each thread
#       Print proc info
#       Run gdb on the binary
#       Attach to the thread
#       Print backtrace
#       Detach thread
#
# mdeacon@zorillaeng.com

import subprocess
import traceback
import sys
import argparse
import ConfigParser
from os import path, access, R_OK
import os
import traceback
import logging
import paramiko
import signal
from logging.handlers import RotatingFileHandler
from zorilla.config import init_config, init_logging
from zorilla.ssh_expect import SSHExpect

logger = logging.getLogger()

def sig_handler(signal, frame):
    logger.error('Ctrl-c pressed...')
    sys.exit()

def backtrace(args):
    sexp = SSHExpect(args.ip_eth0, args.username, args.password)
    resp = ['~]$']
    gdb_resp = ['(gdb)']
    sexp.send_recv('\n', resp)
    i, output = sexp.send_recv('/bin/ps -eLf | grep %s\n' % args.pathname, resp)
    logger.error(output)
    lines = output.split('\n')
    for line in lines:
        #print('line: %s' % line)
        tokens = line.split()
        #print('tokens: %u' % len(tokens))
        if len(tokens) < 10:
            continue
        tid = int(tokens[3])
        separator = '=' * 35
        logger.error('%stid: %u%s' % (separator, tid, separator))
        i, output = sexp.send_recv('cat /proc/%u/status\n' % tid, resp)
        logger.error(output)
        sexp.send_recv('/usr/bin/gdb %s\n' % args.pathname, gdb_resp)
        sexp.send_recv('attach %u\n' % tid, gdb_resp, timeout = 60)
        i, output = sexp.send_recv('bt\n', gdb_resp, timeout = 60)
        logger.error(output)
        sexp.send_recv('detach\n', gdb_resp)
        sexp.send_recv('quit\n', resp)
    
    sexp.close()
    
def main(argv=None):
    # Do argv default this way, as doing it in the functional
    # declaration sets it at compile time.
    if argv is None:
        argv = sys.argv

    # Where this program is installed
    install_path = os.path.dirname(sys.argv[0])
    if len(install_path) == 0:
        install_path = '.'

    # Default configuration
    defaults = {'ip_eth0':'192.168.0.2',
                'username':'root',
                'password':'',
                'loglevel':'ERROR',
                'report':''}

    # Initialize configuration
    # This is common to all test utilities
    parser, remaining_argv = init_config(defaults)

    # Custom parameters
    parser.add_argument("-a", "--ip_eth0", help="IP address for eth0")
    parser.add_argument("-u", "--username", help="username")
    parser.add_argument("-p", "--password", help="password")
    parser.add_argument("pathname", help="Full pathname of binary") 
    args = parser.parse_args(remaining_argv)

    # Set up logging
    # This is common to all test utilities
    init_logging(argv, args, logger)

    # Install Ctrl-C handling
    signal.signal(signal.SIGINT, sig_handler)

    try:
        backtrace(args)
    except Exception as e:
        logger.error('main: Exception: %r', e)
        logger.error('Traceback:\n%s', traceback.format_exc())
        return -1
    
    return 0

if __name__ == '__main__':
    exit(main())

