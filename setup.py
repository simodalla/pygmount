#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import traceback

import pygmount


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

version = pygmount.__version__

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

setup(
    name='pygmount',
    version='0.1.0',
    description='Software for graphical mount network shares.',
    long_description=readme + '\n\n' + history,
    author='Simone Dalla',
    author_email='simodalla@gmail.com',
    url='https://github.com/simodalla/pygmount',
    packages=[
        'pygmount',
    ],
    package_dir={'pygmount': 'pygmount'},
    include_package_data=True,
    install_requires=[
    ],
    entry_points={
        'console_scripts': [
            'mount-smb-shares = pygmount.bin.mount_smb_shares:main'
        ]
    },
    license="BSD",
    zip_safe=False,
    keywords='pygmount samba zenity pyzenity gnome mint',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Environment :: X11 Applications :: GTK',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Other Audience',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Natural Language :: Italian',
        'Operating System :: POSIX :: Linux',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Topic :: Desktop Environment',
        'Topic :: Desktop Environment :: Gnome',
        'Topic :: Office/Business',
        'Topic :: System',
        'Topic :: System :: Networking',
        'Topic :: System :: Shells',
        'Topic :: Utilities',
    ],
    test_suite='tests',
)

print("########")
if 'install' in sys.argv:
    print("*********")
    ABSOLUTE_PATH = '%s' % os.path.abspath(
        os.path.dirname(__file__)).replace('\\', '/')
    desktop_applications = '/usr/share/applications/'
    if os.path.exists(desktop_applications):
        try:
            shutil.copy(ABSOLUTE_PATH + '/media/mount-smb-shares.desktop',
                        desktop_applications)
        except IOError:
            traceback.print_exc(file=sys.stdout)
