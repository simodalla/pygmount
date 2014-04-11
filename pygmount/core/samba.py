# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import os.path
import subprocess
try:
    import apt
except ImportError:
    apt = None


MOUNT_COMMAND_NAME = 'mount'
CIFS_FILESYSTEM_TYPE = 'cifs'


class InstallRequiredPackageError(Exception):

    def __init__(self, msg, original):
        super(InstallRequiredPackageError, self).__init__(msg)
        self.original = original


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
        try:
            output = subprocess.check_output(
                self.command, stderr=subprocess.STDOUT, shell=True)
            return 0, output
        except subprocess.CalledProcessError as e:
            return e.returncode, e.output


class MountSmbShares(object):

    def __init__(self, config_file=None, **kwargs):
        self._required_packages = []

    @property
    def required_packages(self):
        return self._required_packages

    @required_packages.setter
    def required_packages(self, iterable):
        self._required_packages = [element for element in iterable]

    def install_apt_package(self, package_name):
        cache = apt.cache.Cache()
        print(cache)
        try:
            package = cache[package_name]
        except KeyError as ke:
            print("*********")
            msg = ('Il pacchetto "{package}" non e\' presente in questa'
                   ' distribuzione'.format(package=package_name))
            raise InstallRequiredPackageError(msg, ke)

    def install_required_packages(self, package_manager='apt'):
        installed_packages = []
        return installed_packages
