#!/usr/bin/env python
#
# Platform independent expect-like behaviour over RS-232
#
# mdeacon@zorillaeng.com
#

import serial
import logging

logger = logging.getLogger(__name__)

class SerialExpectException(Exception):
    """SerialExpect exceptions
    """
    def __init__(self, value):
        self.value = value
        
    def __str__(self):
        return repr(self.value)

    def __str__(self):
        return str(self.value)

class SerialExpect:
    """Platform independent expect-like behaviour over RS-232
    e.g.:
    sexp = SSHExpect(target, username, password)
    sexp.send('\n')
    sexp.recv(['~]$'])
    sexp.close()
    """

    def __init__(self, port, baudrate=115200, timeout=5):
        """Create a serial connection
        The port is open if no exception occurs
        """
        self.s = serial.Serial(port = port, baudrate = baudrate, timeout = timeout)

    def send(self, cmd):
        """Send a character string to the port
        """
        logger.debug("send: [%s]", cmd);
        self.s.write(cmd)

    def recv(self, resp=[]):
        """Read lines with timeout
        Match output to a list of response
        """
        output = ''
        while True:
            data = self.s.read(1)
            if len(data) == 0:
                logger.debug('recv: read: [%s]', output);
                raise SerialExpectException('recv: Timed out before match for %r in recv' % resp);
            output += data
            # Look for match in output
            i = 0
            for r in resp:
                if r in output:
                    logger.debug('recv: read: [%s]', output);
                    logger.debug('recv: idx %u match: [%s]', i, r);
                    return i
                i += 1

        logger.debug('recv: read: [%s]', output);
        raise SerialExpectException('recv: No match for %r in recv' % resp);

    def send_recv(self, cmd, resp=[], timeout=10):
        """Send a command and expect a response
        """
        self.s.timeout = timeout
        logger.debug('send_recv: cmd: [%s]', cmd)
        logger.debug('send_recv: resp: [%r]', resp)
        self.send(cmd)
        return self.recv(resp);
    
    def close(self):
        self.s.close()


        
