#!/usr/bin/env python
#
# Generic network host
#
# mdeacon@zorillaeng.com
#

import sys
import os
import socket
import logging
import traceback
import paramiko
import time
from paramiko import SSHClient
from scp import SCPClient
from progressbar import ProgressBar
import stat

logger = logging.getLogger(__name__)

class HostException(Exception):
    def __init__(self, value):
        self.parameter = value
        
    def __str__(self):
        return repr(self.parameter)
    
    def __repr__(self):
        return str(self.parameter)

class Host(object):
    """Generic IP host
    """
    def __init__(self, target, username = 'root', password = ''):
        logger.debug('__init__: username %s password %s', username, 
                     password)
        self.target = target
        self.username = username
        self.password = password

    def progress_cb(self, filename, size, sent):
        if sent == 0:
            self.progress_bar = ProgressBar(maxval=size)
            self.progress_bar.start()
        elif size == sent:
            self.progress_bar.finish()
            del(self.progress_bar)
        else:
            self.progress_bar.update(sent)

    def probe_port(self, port):
        """Probe L4 port
        """
        logger.debug('probe_port: ip %s port %u', self.target, port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            rc = sock.connect_ex((self.target, port))
        except Exception as e:
            logger.error('probe_port: Exception: %r', e)
            return -1
        logger.debug('probe_port: sock.connect returned %d', rc)
        sock.close()
        if rc == 0:
            return 0
        return -1

    def command(self, cmd):
        """Issue a command remotely on the host via ssh port 22
        This will output each line in real time to the logger. 
        Makes it look as if the command is running locally
        """
        logger.debug('command(%s)' % cmd)
        output = []
        trans = paramiko.Transport((self.target, 22))
        trans.connect(username=self.username, password=self.password)
        session = trans.open_channel("session")
        fd = session.makefile('rw')
        session.exec_command(cmd)
        rc = 0
        while True:
            temp = fd.readline()
            output.append(temp)
            # Bail out if the string is empty
            if len(temp) == 0:
                fd.close()
                trans.close()
                if len(output) == 0:
                    rc = -1
                break;
            logger.error(temp.strip())
        return rc, output

    def ssh_connect(self):
        """Connect to host via SSH
        """
        sshclient = SSHClient()
        sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        sshclient.load_system_host_keys()
        paramiko.util.log_to_file(os.path.join(os.getcwd(), 'paramiko.log'))
        sys.stdin.flush()
        sys.stdout.flush()
        sys.stderr.flush()
        retry = 0
        retries = 5
        sleep_time = 10
        while True:
            try:
                sshclient.connect(self.target, username = self.username, 
                                  password = self.password)
                logger.debug('ssh_connect: Successfully connected to the target %s',
                             self.target)
                break;
            except Exception as e:
                logger.error('ssh_connect: Exception: %r', e)
                if retry < retries:
                    retry += 1
                    time.sleep(sleep_time)
                    logger.error("ssh_connect: Trying to connect to %s retry %u of %u", 
                                 self.target, retry, retries)
                    continue
                raise
        return sshclient

    def ssh_close(self, sshclient):
        """Disconnect SSH session
        """
        sshclient.close()

    def sshcmd(self, command):
        """Execute a command on the host using SSH
        """
        logger.debug('sshcmd(%s)', command)
        sshclient = self.ssh_connect()

        # Append exit status output to command
        command += '; echo $?'
        stdin, stdout, stderr = sshclient.exec_command(command)
        output = stdout.readlines()
        error = stderr.readlines()
        stdout.flush()
        stderr.flush()
        self.ssh_close(sshclient)
        rc = 0
        # Parse return code from last line in output
        if len(output):
            rc = int(output[-1].strip())
            # Remove this line from the output
            output.pop()
        logger.debug('rc: %r', rc)
        logger.debug('output: %r', output)
        logger.debug('error: %r', error)
        return rc, output, error

    def scpfile(self, remote_file, local_path):
        """ Copy a file from the host to a local directory
        """
        logger.debug('scpfile: remote_file %s local_path %s',
                     remote_file, local_path)
        try:
            sshclient = self.ssh_connect()
        except Exception as e:
            logger.error('scpfile: Exception: %r', e)
            raise

        scp = SCPClient(sshclient.get_transport(), buff_size=1024*1024,
                        socket_timeout=30.0, progress=self.progress_cb)
        try:
            scp.get(remote_file, local_path, preserve_times=True)
            self.ssh_close(sshclient)
        except Exception as e:
            logger.error('scpfile: Exception: %r', e)
            self.ssh_close(sshclient)
            raise
        
        filename = os.path.basename(remote_file)
        local_pathname = os.path.join(local_path, filename)
        os.chmod(local_pathname, stat.S_IRUSR | stat.S_IRGRP | 
                 stat.S_IROTH | stat.S_IWUSR | stat.S_IWGRP | 
                 stat.S_IWOTH | stat.S_IWRITE | stat.S_IREAD)
        return local_pathname

    def scpfileto(self, local_pathname, remote_path):
        """ Copy a given file from a local directory to the host
        """
        logger.debug('scpfileto: local_pathname %s remote_path %s',
                     local_pathname, remote_path)
        try:
            sshclient = self.ssh_connect()
        except Exception as e:
            logger.error('scpfileto: Exception: %r', e)
            raise

        scp = SCPClient(sshclient.get_transport(), buff_size=1024*1024,
                        progress=self.progress_cb)
        try:
            scp.put(local_pathname, remote_path)
            self.ssh_close(sshclient)
        except Exception as e:
            logger.error('scpfileto: Exception: %r', e)
            self.ssh_close(sshclient)
            raise

    def ssh_up(self, retries = 40):
        """Check/wait for SSH to come up
        """
        logger.error('Checking for SSH up...')
        retry = 1
        sleep_time = 5
        while True:
            if (self.probe_port(22) == 0):
                logger.error('SSH is up.')
                return 0
            if retry > retries:
                break
            retry += 1
            time.sleep(sleep_time)
            logger.error('Waiting for SSH up...retry %u of %u', 
                         retry, retries)

        logger.error('SSH not up after %u seconds', retries * sleep_time)
        return -1

    def ssh_down(self, retries = 80):
        """Check/wait for SSH to go down
        """
        logger.error('Checking for SSH down %s...', time.asctime())
        retry = 0
        sleep_time = 3
        while retry < retries:
            if (self.probe_port(22) != 0):
                logger.error('SSH is down.')
                return 0
            retry += 1
            time.sleep(sleep_time)
            logger.error('Waiting for SSH to go down...retry %u of %u %s', 
                         retry, retries, time.asctime())

        logger.error('SSH not down after %u seconds', retries * sleep_time)

