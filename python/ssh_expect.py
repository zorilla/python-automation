#!/usr/bin/env python
#
# Platform independent expect-like behaviour over SSH
#
# mdeacon@zorillaeng.com
#

import paramiko
from paramiko import SSHClient
import logging

logger = logging.getLogger(__name__)

class SSHExpectException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class SSHExpect:
    """Platform independent expect-like behaviour over SSH
    e.g.:
    sexp = SSHExpect(target, username, password)
    sexp.send('\n')
    sexp.recv(['~]$'])
    sexp.close()
    """
    def __init__(self, target, username, password, timeout=10):
        """Open an interactive SSH channel to a host. timeout is in seconds.
        """
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.load_system_host_keys()
        self.client.connect(target, username=username, password=password)
        self.channel = self.client.invoke_shell()
        self.channel.setblocking(1)
        self.channel.settimeout(timeout)

    def send(self, s):
        """Send on channel
        """
        logger.debug('send: [%s]', s)
        bytes_sent = self.channel.send(s)
        if bytes_sent != len(s):
            raise SSHExpectException('bytes_sent: %u != len(s): %u',
                                bytes_sent, len(s))

    def recv(self, resp=[]):
        """Receive from channel
        Return the index of the matched response if any
        """
        logger.debug('recv: exp resp: [%r]', resp)
        i = 0
        output = ''
        while True:
            s = self.channel.recv(nbytes=4096)
            if len(s) == 0:
                break
            logger.debug('recv: got resp: [%s]', s)
            output += s
            i = 0
            for r in resp:
                if r in output:
                    logger.debug('recv: match resp: [%s]' % r)
                    return i, output
                i += 1
        logger.error(output)
        raise SSHExpectException('recv: no match')

    def send_recv(self, cmd, resp=[], timeout=10):
        """Combine send and receive in a single call
        """
        self.channel.settimeout(timeout)
        logger.debug('send_recv: cmd [%s]' % cmd)
        logger.debug('send_recv: resp [%r]', resp)
        self.send(cmd)
        return self.recv(resp)

    def close(self):
        """Close the channel and SSH client
        """
        if self.channel.exit_status_ready():
            rc = self.channel.recv_exit_status()
            logger.debug('channel.recv_exit_status() returned %d', rc)
        else:
            logger.debug('channel.exit_status_ready() returned False')
        self.channel.close()
        self.client.close()
