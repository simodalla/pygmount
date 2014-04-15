# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import collections
import os.path
import subprocess
try:
    import apt
except ImportError:
    apt = None
try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser


MOUNT_COMMAND_NAME = 'mount'
CIFS_FILESYSTEM_TYPE = 'cifs'


class InstallRequiredPackageError(Exception):

    def __init__(self, msg, source):
        super(InstallRequiredPackageError, self).__init__(msg)
        self.source = source


def run_command(command):
    """
    Utility function for run command with subprocess. Return a tuple, with
    return code and if python >= 2.7 command's output or None if python <= 2.6
    """
    try:
        check_ouput = getattr(
            subprocess, 'check_output', subprocess.check_call)
        result = check_ouput(command, stderr=subprocess.STDOUT, shell=True)
        if check_ouput.__name__ == 'check_output':
            return 0, result
        else:
            return result, None
    except subprocess.CalledProcessError as e:
        return e.returncode, getattr(e, 'output', None)


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


class MountSmbShares(object):

    def __init__(self, config_file='~/.pygmount.rc'):
        self._shares = None
        self._config_file = None
        self._required_packages = None
        self.config_file = config_file

    @property
    def required_packages(self):
        return self._required_packages

    @required_packages.setter
    def required_packages(self, iterable):
        self._required_packages = [element for element in iterable]

    @property
    def config_file(self):
        return self._config_file

    @config_file.setter
    def config_file(self, config_file):
        self._config_file = os.path.expanduser(config_file)

    def install_apt_package(self, package_name):
        cache = apt.cache.Cache()
        try:
            package = cache[package_name]
            if not package.is_installed:
                try:
                    package.mark_install()
                    cache.commit()
                except apt.LockFailedException as lfe:
                    msg = (
                        'Impossibile installare i pacchetti richiesti con un '
                        ' utente che non ha diritti amministrativi.')
                    raise InstallRequiredPackageError(msg, lfe)
                except Exception as e:
                    msg = (
                        'Errore genrico nell\'installazione del pacchetto'
                        ' "{package}".'.format(package=package_name))
                    raise InstallRequiredPackageError(msg, e)
        except KeyError as ke:
            msg = ('Il pacchetto "{package}" non e\' presente in questa'
                   ' distribuzione.'.format(package=package_name))
            raise InstallRequiredPackageError(msg, ke)

    @property
    def shares(self):
        return self._shares

    def set_shares(self):
        self._shares = []
        config = ConfigParser()
        config.read(self.config_file)
        for share in config.sections():
            wrapper_args = [None, None, None]
            wrapper_kwargs = {}
            hooks = [None, None]
            for key, value in config.items(share):
                if key == 'hostname':
                    if '@' not in value:
                        wrapper_args[0] = value
                    else:
                        hostname, credentials = (item[::-1] for item
                                                 in value[::-1].split('@', 1))
                        wrapper_args[0] = hostname
                        credentials = tuple(cred.lstrip('"').rstrip('"')
                                            for cred in
                                            credentials.split(':', 1))
                        wrapper_kwargs.update({'username': credentials[0]})
                        if len(credentials) > 1:
                            wrapper_kwargs.update({'password': credentials[1]})
                elif key == 'share':
                    wrapper_args[1] = value
                elif key == 'mountpoint':
                    wrapper_args[2] = value
                elif key == 'hook_pre_command':
                    hooks[0] = value
                elif key == 'hook_post_command':
                    hooks[1] = value
                else:
                    wrapper_kwargs.update({key: value})
            self._shares.append(
                (share, MountCifsWrapper(*wrapper_args, **wrapper_kwargs),)
                + tuple(hooks))

    def run(self):
        for package in self.required_packages:
            try:
                self.install_apt_package(package)
            except InstallRequiredPackageError as irpe:
                if isinstance(irpe.source, apt.LockFailedException):
                    return 1



