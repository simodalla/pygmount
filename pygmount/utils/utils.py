# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, absolute_import

import os
import platform
import ConfigParser


def get_sudo_username():
    """
    Check 'SUDO_USER' var if in environment and return a tuple with True and value of 'SUDO_USER' if
    the var in environment or a tuple with False and 'USER' value.

    Return tuple.
    """
    if 'SUDO_USER' in os.environ:
        return True, os.environ['SUDO_USER']
    return False, os.environ['USER']


def get_home_dir():
    """
    Return path of user's home directory.

    Return string.
    """
    system = platform.system().lower()
    if system == 'linux':
        return '/home/'
    elif system == 'darwin':
        return '/Users/'
    elif system == 'windows':
        return 'C:/Documents...'
    else:
        raise Exception("Impossibile individuare il tipo di sistema")


def read_config(file=None):
    """
    Read a config file into .ini format and return dict of shares.

    Keyword arguments:
    file -- the path of config file (default None)

    Return dict.
    """
    if not os.path.exists(file):
        raise IOError('Impossibile trovare il file %s' % file)
    shares = []
    config = ConfigParser.ConfigParser()
    config.read(file)
    for share_items in [config.items(share_title) for share_title in
                        config.sections()]:
        dict_share = {}
        for k, v in share_items:
            dict_share.update({k: v})
        shares.append(dict_share)
    return shares


def install_media():
    from pkg_resources import Requirement, resource_filename

    # Get our file.
    filename = resource_filename(Requirement.parse("Project"),
                                 "config/config.sample.xml")

    try:
        import shutil

        # Create the directory.
        if not os.path.exists("/etc/myproject"):
            os.mkdir("/etc/myproject")

        # Copy the source file. Don't clobber existing files.
        if not os.path.exists("/etc/myproject/config.xml"):
            shutil.copyfile(filename, "/etc/myproject/config.xml")

    except IOError:
        print(
            "Unable to copy configuration file to /etc/myproject/config.xml.")

