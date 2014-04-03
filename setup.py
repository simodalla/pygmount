#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil

import pygmount

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

version = pygmount.__version__

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    print("You probably want to also tag the version now:")
    print("  git tag -a %s -m 'version %s'" % (version, version))
    print("  git push --tags")
    sys.exit()

readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')
name = 'pygmount'

setup(
    name=name,
    version=version,
    description='Software for graphical mount network shares.',
    long_description=readme + '\n\n' + history,
    author='Simone Dalla',
    author_email='simodalla@gmail.com',
    url='https://github.com/simodalla/pygmount',
    packages=find_packages(),
    package_dir={'pygmount': 'pygmount'},
    include_package_data=True,
    install_requires=['PyZenity==0.1.7'],
    dependency_links=[
        "http://brianramos.com/software/PyZenity/PyZenity-0.1.7.tar.gz#egg=PyZenity-0.1.7"
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
        'Development Status :: 4 - Beta',
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


if 'install' in sys.argv:
    from pkg_resources import Requirement, resource_filename

    filename = resource_filename(Requirement.parse(name),
                                 'pygmount/media/mount-smb-shares.desktop')
    desktop_applications = '/usr/share/applications/'
    if os.path.exists(desktop_applications):
        try:
            shutil.copy(filename, desktop_applications)
            print('#### File "{}" successfully installed into "{}"'
                  ' ####'.format(filename, desktop_applications))
        except IOError as e:
            print('#### Error! Impossible copy "{}": {}. ####'.format(
                filename, e))
    else:
        print('#### Error! Directory "{}" not exist. ####'.format(
            desktop_applications))
