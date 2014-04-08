#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

try:
    import unittest
except ImportError:
    import unittest2 as unittest

from pygmount.core.samba import MountCifsWrapper


class MountCifsWrapperTest(unittest.TestCase):
    def setUp(self):
        self.server = 'server.example.com'
        self.share = 'share_1'
        self.mountpoint = '/mnt/mountpoint'

    def test_setter_option(self):
        wrapper = MountCifsWrapper(self.server, self.share, self.mountpoint)
        options = {'foo': 'bar'}
        wrapper.options = options
        self.assertEqual(wrapper._options, [('foo', 'bar')])

    def test_init_with_default_type(self):
        wrapper = MountCifsWrapper(self.server, self.share, self.mountpoint)
        self.assertEqual(wrapper.command_name, 'mount')
        self.assertEqual(wrapper.filesystem_type, 'cifs')
        self.assertEqual(wrapper.server, self.server)
        self.assertEqual(wrapper.share, self.share)
        self.assertEqual(wrapper.mountpoint, self.mountpoint)
        self.assertEqual(wrapper._options, [])

    def test_getter_service(self):
        wrapper = MountCifsWrapper(self.server, self.share, self.mountpoint)
        self.assertEqual(wrapper.service,
                         '//{self.server}/{self.share}'.format(self=self))

    def test_getter_options_with_none_option(self):
        option = 'foo'
        options = {option: None}
        wrapper = MountCifsWrapper(self.server, self.share, self.mountpoint)
        wrapper.options = options
        self.assertEqual(wrapper.options, '-o {option}'.format(option=option))

    def test_get_command_without_options(self):
        wrapper = MountCifsWrapper(self.server, self.share, self.mountpoint)
        self.assertEqual(
            wrapper.command,
            'mount -t cifs {wrapper.service} {wrapper.mountpoint}'.format(
                wrapper=wrapper))

    def test_get_command_with_option_that_is_none(self):
        options = {'option1': None}
        wrapper = MountCifsWrapper(self.server, self.share, self.mountpoint,
                                   **options)
        self.assertEqual(
            wrapper.command,
            'mount -t cifs {wrapper.service} {wrapper.mountpoint}'.format(
                wrapper=wrapper))



if __name__ == '__main__':
    unittest.main()
