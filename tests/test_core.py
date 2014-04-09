#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from pygmount.core.samba import MountCifsWrapper


class MountCifsWrapperTest(unittest.TestCase):
    def setUp(self):
        self.server = 'server.example.com'
        self.share = 'share_1'
        self.mountpoint = '/mnt/mountpoint'

    def _check_options(self, text_options, **kwargs):
        self.assertTrue(text_options.startswith('-o'))
        options = text_options.split('-o')[1].strip().split(',')
        for option in kwargs:
            text_option = ('{option}={value}'.format(option=option,
                                                     value=kwargs[option])
                           if kwargs[option] else option)
            self.assertIn(text_option, options)

    def test_options_setter(self):
        wrapper = MountCifsWrapper(self.server, self.share, self.mountpoint)
        options = {'foo': 'bar'}
        wrapper.options = options
        self.assertEqual(wrapper._options, options)

    def test_options_getter_with_option_that_is_none(self):
        option = 'foo'
        options = {option: None}
        wrapper = MountCifsWrapper(self.server, self.share, self.mountpoint)
        wrapper.options = options
        self._check_options(wrapper.options, **options)

    def test_options_getter_with_option_with_value(self):
        options = {'foo': 'bar'}
        wrapper = MountCifsWrapper(self.server, self.share,
                                   self.mountpoint)
        wrapper.options = options
        self._check_options(wrapper.options, **options)

    def test_options_getter_with_option_with_value_and_none_option(self):
        options = {'foo': 'bar', 'foo1': None}
        wrapper = MountCifsWrapper(self.server, self.share,
                                   self.mountpoint)
        wrapper.options = options
        self._check_options(wrapper.options, **options)

    def test_init_with_empty_kwargs(self):
        wrapper = MountCifsWrapper(self.server, self.share, self.mountpoint)
        self.assertEqual(wrapper.command_name, 'mount')
        self.assertEqual(wrapper.filesystem_type, 'cifs')
        self.assertEqual(wrapper.server, self.server)
        self.assertEqual(wrapper.share, self.share)
        self.assertEqual(wrapper.mountpoint, self.mountpoint)
        self.assertEqual(wrapper._options, {})

    def test_service_getter(self):
        wrapper = MountCifsWrapper(self.server, self.share, self.mountpoint)
        self.assertEqual(wrapper.service,
                         '//{self.server}/{self.share}'.format(self=self))

    def test_command_getter_without_options(self):
        wrapper = MountCifsWrapper(self.server, self.share, self.mountpoint)
        self.assertTrue(
            wrapper.command,
            'mount -t cifs {wrapper.service} {wrapper.mountpoint}'.format(
                wrapper=wrapper))

    def test_command_getter_with_options(self):
        options = {'foo': None}
        wrapper = MountCifsWrapper(self.server, self.share, self.mountpoint,
                                   **options)
        command_without_options = (
            'mount -t cifs {wrapper.service} {wrapper.mountpoint}'.format(
                wrapper=wrapper))
        self._check_options(
            wrapper.command.replace(command_without_options, '').strip(),
            **options)

    def test_contains_return_true(self):
        options = {'foo': None}
        wrapper = MountCifsWrapper(self.server, self.share, self.mountpoint,
                                   **options)
        self.assertTrue('foo' in wrapper)

    def test_contains_return_false(self):
        wrapper = MountCifsWrapper(self.server, self.share,
                                   self.mountpoint)
        self.assertFalse('fake' in wrapper)

    def test_getitem_return_option(self):
        options = {'foo': 'bar'}
        wrapper = MountCifsWrapper(self.server, self.share, self.mountpoint,
                                   **options)
        self.assertEqual(wrapper['foo'], 'bar')

    def test_setitem_set_option(self):
        wrapper = MountCifsWrapper(self.server, self.share,
                                   self.mountpoint)
        wrapper['foo'] = 'bar'
        self.assertIn(('foo', 'bar'), wrapper._options.items())

