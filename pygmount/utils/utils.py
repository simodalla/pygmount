# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, absolute_import

import os
import platform
try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser


def get_sudo_username():
    """
    Check 'SUDO_USER' var if in environment and return a tuple with True and
    value of 'SUDO_USER' if the var in environment or a tuple with False and
    'USER' value.

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


def read_config(filename=None):
    """
    Read a config filename into .ini format and return dict of shares.

    Keyword arguments:
    filename -- the path of config filename (default None)

    Return dict.
    """
    if not os.path.exists(filename):
        raise IOError('Impossibile trovare il filename %s' % filename)
    shares = []
    config = ConfigParser()
    config.read(filename)
    for share_items in [config.items(share_title) for share_title in
                        config.sections()]:
        dict_share = {}
        for key, value in share_items:
            if key == 'hostname' and '@' in value:
                hostname, credentials = (item[::-1] for item
                                         in value[::-1].split('@', 1))
                dict_share.update({key: hostname})
                credentials = tuple(cred.lstrip('"').rstrip('"')
                                    for cred in credentials.split(':', 1))
                dict_share.update({'username': credentials[0]})
                if len(credentials) > 1:
                    dict_share.update({'password': credentials[1]})
                continue
            dict_share.update({key: value})
        shares.append(dict_share)
    return shares
