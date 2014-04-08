# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import os.path
from collections import MutableMapping


class MountCifsWrapper(object):
    command_name = 'mount'
    filesystem_type = 'cifs'

    def __init__(self, server, share, mountpoint, **kwargs):
        self.server = server
        self.share = share
        self.mountpoint = mountpoint
        self.options = kwargs

    @property
    def command(self):
        command = ('{self.command_name} -t {self.filesystem_type}'
                   ' {self.service} {self.mountpoint}'.format(self=self))
        return command

    @property
    def service(self):
        return '//{path}'.format(path=os.path.join(self.server, self.share))

    # def get_option(self, option):
    #     return self.options

    @property
    def options(self):
        result = '-o'
        for option, value in self._options:
            result += (' {}={}'.format(option, value) if value
                       else ' {}'.format(option))
        return result

    @options.setter
    def options(self, options):
        self._options = [(key, options[key]) for key in options]


