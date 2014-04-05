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
        self.options = {}
        # for sel

    @property
    def command(self):
        command = ('{self.command_name} -t {self.filesystem_type}'
                   ' {self.service} {self.mountpoint}'.format(self=self))
        return command

    @property
    def service(self):
        return '//{}'.format(os.path.join(self.server, self.share))

    @property
    def option(self):
        return self.options

    # @option

    # @options.setter
    # def options(self, kwargs):
    #     print("SETTER", kwargs)
    #     self.options =


