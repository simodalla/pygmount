# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import os.path
import subprocess


MOUNT_COMMAND_NAME = 'mount'
CIFS_FILESYSTEM_TYPE = 'cifs'


class MountCifsWrapper(object):

    def __init__(self, server, share, mountpoint, filesystem_type=None,
                 **kwargs):
        self.command_name = MOUNT_COMMAND_NAME
        self.filesystem_type = CIFS_FILESYSTEM_TYPE
        self.server = server
        self.share = share
        self.mountpoint = mountpoint
        self.options = kwargs

    @property
    def command(self):
        command = ('{self.command_name} -t {self.filesystem_type}'
                   ' {self.service} {self.mountpoint}'.format(self=self))
        if self.options:
            command += ' ' + self.options
        return command

    @property
    def service(self):
        return '//{path}'.format(path=os.path.join(self.server, self.share))

    @property
    def options(self):
        if self._options:
            return '-o ' + ','.join([
                '{o}={v}'.format(o=option, v=self._options[option])
                if self._options[option] else '{o}'.format(o=option)
                for option in self._options])

    @options.setter
    def options(self, options):
        self._options = options.copy()

    def __contains__(self, item):
        return True if item in self._options else False

    def __getitem__(self, item):
        return self._options[item]

    def __setitem__(self, key, value):
        self._options[key] = value

    def run_command(self):
        process = subprocess.Popen(self.command, shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        retcode = process.wait()
