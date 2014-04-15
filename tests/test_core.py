#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

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
                                 InstallRequiredPackageError, run_command)


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
def get_fake_apt_cache(list_packages_data=None, commit=True):
    mock_apt = Mock()
    mock_apt.LockFailedException = FakeLockFailedException
    if list_packages_data:
        cache = FakeCache(commit=commit)
        mock_apt._cache = cache
        for data in list_packages_data:
            cache[data[0]] = data[1:]
        mock_apt.cache.Cache.return_value = cache
    return mock_apt


def get_fake_configparser(config_data):
    class FakeConfigParser(object):
        def __init__(self):
            self._data = list(config_data)

        def read(self, filename):
            pass

        def sections(self):
            return [d[0] for d in self._data]

        def items(self, section):
            for k, values in self._data:
                if k == section:
                    return values.items()
    return FakeConfigParser


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


class RunCommandTest(unittest.TestCase):

    def setUp(self):
        self.command = 'ln -s'

    @patch('pygmount.core.samba.subprocess')
    def test_run_command_with_check_output_function(
            self, mock_subprocess):
        check_output = Mock()
        check_output.__name__ = 'check_output'
        mock_subprocess.check_output = check_output
        run_command(self.command)
        check_output.assert_called_once_with(
            self.command, stderr=mock_subprocess.STDOUT, shell=True)

    @patch('pygmount.core.samba.subprocess', autospec=True)
    def test_run_command_with_check_call_function(
            self, mock_subprocess):
        mock_subprocess.check_call.__name__ = 'check_call'
        if 'check_output' in dir(mock_subprocess):
            mock_subprocess.check_output = mock_subprocess.check_call
        run_command(self.command)

        mock_subprocess.check_call.assert_called_once_with(
            self.command, stderr=mock_subprocess.STDOUT, shell=True)

    @patch('pygmount.core.samba.subprocess')
    def test_run_command_check_output_return_tuple(
            self, mock_subprocess):
        check_output = Mock()
        check_output.__name__ = 'check_output'
        check_output.return_value = 'command output'
        mock_subprocess.check_output = check_output
        result = run_command(self.command)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[1], check_output.return_value)

    @patch('pygmount.core.samba.subprocess', autospec=True)
    def test_run_command_check_call_return_tuple(
            self, mock_subprocess):
        mock_subprocess.check_call.__name__ = 'check_call'
        mock_subprocess.check_call.return_value = 0
        if 'check_output' in dir(mock_subprocess):
            mock_subprocess.check_output = mock_subprocess.check_call
        result = run_command(self.command)
        self.assertEqual(result[0], 0)
        self.assertIsNone(result[1])

    @patch('pygmount.core.samba.subprocess')
    def test_run_command_in_check_output_occours_exception(
            self, mock_subprocess):
        check_output = Mock()
        mock_subprocess.CalledProcessError = subprocess.CalledProcessError
        check_output.side_effect = subprocess.CalledProcessError(1,
                                                                 self.command)
        result = run_command(self.command)
        self.assertEqual(result[0], 1)
        self.assertIsNone(result[1])

    @patch('pygmount.core.samba.subprocess', autospec=True)
    def test_run_command_in_check_output_occours_exception(
            self, mock_subprocess):
        mock_subprocess.CalledProcessError = subprocess.CalledProcessError
        mock_subprocess.check_call.side_effect = subprocess.CalledProcessError(
            1, self.command)
        if 'check_output' in dir(mock_subprocess):
            mock_subprocess.check_output = mock_subprocess.check_call
        result = run_command(self.command)
        self.assertEqual(result[0], 1)
        self.assertIsNone(result[1])


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

    @patch('pygmount.core.samba.apt')
    @patch('pygmount.core.samba.MountSmbShares.install_apt_package')
    def test_run_failed_for_apt_lock_failed(self, mock_install_apt, mock_apt):
        """
        Test that run return 1 if into an install_apt_package method
        occurs an apt.LockFailedException exception
        """
        mss = MountSmbShares()
        mss.required_packages = ['package1']
        mock_apt.LockFailedException = FakeLockFailedException
        mock_install_apt.side_effect = (
            InstallRequiredPackageError(
                "IRPE", source=FakeLockFailedException("FLFE")))
        self.assertEqual(mss.run(), 1)

    @patch('pygmount.core.samba.MountCifsWrapper')
    def test_read_config_parser_simple(self, mock_wrapper):
        data = [('absoluthe_share', {'hostname': 'server_windows.example',
                                     'share': 'condivisione',
                                     'mountpoint': '/mnt/mountpoint'})]
        with patch('pygmount.core.samba.ConfigParser',
                   get_fake_configparser(data)):
            mss = MountSmbShares()
            mss.set_shares()
            mock_wrapper.assert_called_once_with(data[0][1]['hostname'],
                                                 data[0][1]['share'],
                                                 data[0][1]['mountpoint'])
            self.assertEqual(len(mss.shares), 1)
            self.assertEqual(mss.shares[0][0], data[0][0])
            self.assertIsNone(mss.shares[0][2])
            self.assertIsNone(mss.shares[0][3])

    @patch('pygmount.core.samba.MountCifsWrapper')
    def test_read_config_parser_with_only_username(self, mock_wrapper):
        username = 'user1'
        hostname = 'server_windows.example'
        data = [('absoluthe_share',
                 {'hostname': username + '@' + hostname,
                  'share': 'condivisione',
                  'mountpoint': '/mnt/mountpoint'})]
        with patch('pygmount.core.samba.ConfigParser',
                   get_fake_configparser(data)):
            mss = MountSmbShares()
            mss.set_shares()
            mock_wrapper.assert_called_once_with(hostname,
                                                 data[0][1]['share'],
                                                 data[0][1]['mountpoint'],
                                                 username=username)
            self.assertEqual(len(mss.shares), 1)
            self.assertEqual(mss.shares[0][0], data[0][0])

    @patch('pygmount.core.samba.MountCifsWrapper')
    def test_read_config_parser_with_only_username_and_password(
            self, mock_wrapper):
        username = 'user1'
        password = 'password'
        hostname = 'server_windows.example'
        data = [('absoluthe_share',
                 {'hostname': username + ':' + password + '@' + hostname,
                  'share': 'condivisione',
                  'mountpoint': '/mnt/mountpoint'})]
        with patch('pygmount.core.samba.ConfigParser',
                   get_fake_configparser(data)):
            mss = MountSmbShares()
            mss.set_shares()
            mock_wrapper.assert_called_once_with(hostname,
                                                 data[0][1]['share'],
                                                 data[0][1][
                                                     'mountpoint'],
                                                 username=username,
                                                 password=password)
            self.assertEqual(len(mss.shares), 1)
            self.assertEqual(mss.shares[0][0], data[0][0])

    @patch('pygmount.core.samba.MountCifsWrapper')
    def test_read_config_parser_with_options(self, mock_wrapper):
        options = {'option_1': 'option_1', 'option_2': 'option_2'}
        data = [
            ('absoluthe_share', {'hostname': 'server_windows.example',
                                 'share': 'condivisione',
                                 'mountpoint': '/mnt/mountpoint'})]
        data[0][1].update(options)
        with patch('pygmount.core.samba.ConfigParser',
                   get_fake_configparser(data)):
            mss = MountSmbShares()
            mss.set_shares()
            mock_wrapper.assert_called_once_with(
                data[0][1]['hostname'],
                data[0][1]['share'],
                data[0][1]['mountpoint'],
                **options)
            self.assertEqual(len(mss.shares), 1)
            self.assertEqual(mss.shares[0][0], data[0][0])

    @patch('pygmount.core.samba.MountCifsWrapper')
    def test_read_config_parser_with_hook_pre_command(self, mock_wrapper):
        hook = {'hook_pre_command': 'ls -l'}
        data = [('absoluthe_share', {'hostname': 'server_windows.example',
                                     'share': 'condivisione',
                                     'mountpoint': '/mnt/mountpoint'})]
        data[0][1].update(hook)
        with patch('pygmount.core.samba.ConfigParser',
                   get_fake_configparser(data)):
            mss = MountSmbShares()
            mss.set_shares()
            mock_wrapper.assert_called_once_with(data[0][1]['hostname'],
                                                 data[0][1]['share'],
                                                 data[0][1]['mountpoint'])
            self.assertEqual(len(mss.shares), 1)
            self.assertEqual(mss.shares[0][2], list(hook.values())[0])

    @patch('pygmount.core.samba.MountCifsWrapper')
    def test_read_config_parser_with_hook_post_command(self, mock_wrapper):
        hook = {'hook_post_command': 'ls -l'}
        data = [
            ('absoluthe_share', {'hostname': 'server_windows.example',
                                 'share': 'condivisione',
                                 'mountpoint': '/mnt/mountpoint'})]
        data[0][1].update(hook)
        with patch('pygmount.core.samba.ConfigParser',
                   get_fake_configparser(data)):
            mss = MountSmbShares()
            mss.set_shares()
            mock_wrapper.assert_called_once_with(
                data[0][1]['hostname'],
                data[0][1]['share'],
                data[0][1]['mountpoint'])
            self.assertEqual(len(mss.shares), 1)
            self.assertEqual(mss.shares[0][3], list(hook.values())[0])
