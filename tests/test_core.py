#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import unittest

from pygmount.core.samba import MountCifsWrapper


class MountCifsWrapperTest(unittest.TestCase):
    def setUp(self):
        self.server = 'server.example.com'
        self.share = 'share_1'
        self.mountpoint = '/mnt/mountpoint'

    def test_init_with_default_type(self):
        wrapper = MountCifsWrapper(self.server, self.share, self.mountpoint)
        self.assertEqual(wrapper.command_name, 'mount')
        self.assertEqual(wrapper.filesystem_type, 'cifs')
        self.assertEqual(wrapper.server, self.server)
        self.assertEqual(wrapper.share, self.share)
        self.assertEqual(wrapper.mountpoint, self.mountpoint)

    def test_service_property(self):
        wrapper = MountCifsWrapper(self.server, self.share, self.mountpoint)
        self.assertEqual(wrapper.service, '//{}/{}'.format(self.server,
                                                           self.share))

    def test_get_command_whitout_options(self):
        wrapper = MountCifsWrapper(self.server, self.share, self.mountpoint)
        self.assertEqual(
            wrapper.command,
            'mount -t cifs {wrapper.service} {wrapper.mountpoint}'.format(
                wrapper=wrapper))


if __name__ == '__main__':
    unittest.main()
