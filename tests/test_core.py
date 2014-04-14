#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import subprocess
import sys
import pytest


try:
    import unittest2 as unittest
except ImportError:
    import unittest
try:
    from mock import patch, Mock, MagicMock
except ImportError:
    from unittest.mock import patch, Mock

from pygmount.core.samba import (MountCifsWrapper, MountSmbShares,
                                 InstallRequiredPackageError)


def get_fake_check_output(return_code=0, return_out='out'):
    check_output = Mock()
    if return_code == 0:
        check_output.return_value = return_out
    else:
        try:
            # >= python 2.7
            check_output.side_effect = subprocess.CalledProcessError(
                return_code, 'command', return_out)
        except TypeError:
            # python 2.6
            check_output.side_effect = subprocess.CalledProcessError(
                return_code, 'command')
    return check_output


class FakeLockFailedException(Exception):
    pass


class FakeCache(object):
    def __init__(self, commit=True):
        self.packages = {}
        self._commit = commit

    def __getitem__(self, item):
        return self.packages[item]

    def __setitem__(self, key, value):
        """
        key = package_name
        value = tuple(boolean for is_installed, ...)
        """
        mock = Mock()
        mock.is_installed = value[0]
        mock.mark_install.return_value = True
        self.packages[key] = mock

    def commit(self):
        if isinstance(self._commit, Exception):
            raise self._commit
        return self._commit


# [(package, True, Exception),..]
def get_fake_apt_cache(list_packages_data, commit=True):
    mock_apt = Mock()
    mock_apt.LockFailedException = FakeLockFailedException
    cache = FakeCache(commit=commit)
    mock_apt._cache = cache
    for data in list_packages_data:
        cache[data[0]] = data[1:]
    mock_apt.cache.Cache.return_value = cache
    return mock_apt


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

    @pytest.mark.skipif(sys.version_info <= (2, 7),
                        reason="requiresat least python2.7")
    @patch('pygmount.core.samba.subprocess.check_output')
    def test_run_command_call_subprocess_and_wait(self, mock_check_output):
        options = {'foo': 'bar'}
        wrapper = MountCifsWrapper(self.server, self.share, self.mountpoint,
                                   **options)
        wrapper.run_command()
        mock_check_output.assert_is_called_once(wrapper.command,
                                                stderr=subprocess.STDOUT,
                                                shell=True)

    @pytest.mark.skipif(sys.version_info <= (2, 7),
                        reason="requiresat least python2.7")
    @patch('pygmount.core.samba.subprocess.check_output',
           get_fake_check_output(0, 'out'))
    def test_run_command_with_subprocess_ok(self):
        options = {'foo': 'bar'}
        wrapper = MountCifsWrapper(self.server, self.share, self.mountpoint,
                                   **options)
        return_code, output = wrapper.run_command()
        self.assertEqual(return_code, 0)
        self.assertEqual(output, 'out')

    @pytest.mark.skipif(sys.version_info <= (2, 7),
                        reason="requires at least python2.7")
    @patch('pygmount.core.samba.subprocess.check_output',
           get_fake_check_output(1, 'error'))
    def test_run_command_with_subprocess_ko(self):
        options = {'foo': 'bar'}
        wrapper = MountCifsWrapper(self.server, self.share, self.mountpoint,
                                   **options)
        return_code, output = wrapper.run_command()
        self.assertEqual(return_code, 1)
        self.assertEqual(output, 'error')


class MountSmbSharesTest(unittest.TestCase):

    def test_apt_pkg_requirements_setter(self):
        mss = MountSmbShares()
        packages = ['package1', 'package2']
        mss.required_packages = packages
        self.assertIsInstance(mss._required_packages, list)
        self.assertListEqual(mss._required_packages, packages)

    def test_apt_pkg_requirements_getter_setter(self):
        mss = MountSmbShares()
        packages = ['package1', 'package2']
        mss.required_packages = packages
        self.assertListEqual(mss.required_packages, packages)

    @patch('pygmount.core.samba.apt',
           get_fake_apt_cache([('package1', True)]))
    def test_install_apt_package_with_package_not_in_cache(self):
        mss = MountSmbShares()
        package = 'fake_package'
        self.assertRaises(InstallRequiredPackageError,
                          mss.install_apt_package, package)

    @patch('pygmount.core.samba.apt',
           get_fake_apt_cache([('package1', True)]))
    def test_install_apt_package_with_package_already_installed(self):
        mss = MountSmbShares()
        package = 'package1'
        self.assertIsNone(mss.install_apt_package(package))

    @patch('pygmount.core.samba.apt', get_fake_apt_cache(
        [('package1', False)], commit=FakeLockFailedException()))
    def test_install_apt_package_raise_exception_lock_failed(self):
        mss = MountSmbShares()
        package = 'package1'
        with pytest.raises(InstallRequiredPackageError) as e:
            mss.install_apt_package(package)
        self.assertIsInstance(e.value.source, FakeLockFailedException)
        self.assertEqual(str(e.value),
                         'Impossibile installare i pacchetti richiesti con un '
                         ' utente che non ha diritti amministrativi.')

    @patch('pygmount.core.samba.apt', get_fake_apt_cache(
        [('package1', False)], commit=Exception()))
    def test_install_apt_package_raise_generic_exception(self):
        mss = MountSmbShares()
        package = 'package1'
        with pytest.raises(InstallRequiredPackageError) as e:
            mss.install_apt_package(package)
        self.assertIsInstance(e.value.source, Exception)
        self.assertEqual(str(e.value),
                         'Errore genrico nell\'installazione del pacchetto'
                         ' "{package}".'.format(package=package))
