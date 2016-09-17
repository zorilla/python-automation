#!/usr/bin/env python
#
# Example demonstrating use of SSHExpect and SerialExpect
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
import signal
import traceback
from zorilla.config import init_config, init_logging
from zorilla.ssh_expect import SSHExpect
from zorilla.serial_expect import SerialExpect
from zorilla.host import Host

logger = logging.getLogger()

def sig_handler(signal, frame):
    logger.error('Ctrl-c pressed...')
    sys.exit()

def serial_expect_example(args):
    """Connect to a Linux host over RS-232
    List files at the root directory
    """
    logger.error('serial_example...')
    sexp = SerialExpect(args.serial_port, args.baud_rate)
    idx = sexp.send_recv('\n', ['login:', '~]$'])
    if idx == 0:
        idx = sexp.send_recv(args.username + '\n', ['Password', '~]$'])
        if idx == 0:
            sexp.send_recv(args.password + '\n', ['~]$'])
    sexp.send_recv('/sbin/ls /l\n', ['~]$'])
    sexp.close()

def ssh_expect_example(args):
    """Connect to a Linux host over SSH
    List files at the root directory
    """
    logger.error('ssh_example...')
    sexp = SSHExpect(args.ip_eth0, args.username, args.password)
    sexp.send_recv(args.password + '\n', ['~]$'])
    sexp.send_recv('/bin/ls -l /\n', ['~]$'])
    sexp.close()

def example(args):
    """Call example functions
    """
    #serial_expect_example(args)
    ssh_expect_example(args)
    serial_expect_example(args)

def main(argv=None):
    # Do argv default this way, as doing it in the functional
    # declaration sets it at compile time.
    if argv is None:
        argv = sys.argv

    # Default configuration
    defaults = {'serial_port':'COM1',
                'baud_rate':'115200',
                'ip_eth0':'192.168.2.68',
                'gateway':'192.168.1.1',
                'netmask':'255.255.248.0',
                'username':'root',
                'password':'',
                'loglevel':'ERROR',
                'report':''}

    # Initialize configuration
    # This is common to all test utilities
    parser, remaining_argv = init_config(defaults)

    # Custom parameters
    parser.add_argument("-a", "--ip_eth0", help="IP address for eth0")
    parser.add_argument("-u", "--username", help="Username")
    parser.add_argument("-p", "--password", help="Username")
    args = parser.parse_args(remaining_argv)

    # Set up logging
    init_logging(argv, args, logger)

    # Install Ctrl-C handling
    signal.signal(signal.SIGINT, sig_handler)
    logger.error('Example SSH Expect.')
    try:
        example(args)
    except Exception as e:
        logger.error('Exception: %r', e)
        logger.error('Traceback:\n%s', traceback.format_exc())
        return -1

    return 0

if __name__ == '__main__':
    exit(main())

    
