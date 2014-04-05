#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import sys
import optparse
from pygmount.utils.mount import MountSmbShares


def main():
    description_msg = u'Mount samba shares into Samba Domain'
    p = optparse.OptionParser(description=description_msg,
                              prog='mount-smb-shares',
                              version='0.1.1',
                              usage="%prog [options]")
    p.add_option("--verbose", "-v", action="store_true",
                 default=False, help="Enables verbose output")
    p.add_option("--file", "-f", action="store",
                 default=None, help="Path's mount shares file")
    p.add_option("--dry-run", "-n", action="store_true",
                 default=False, dest='dry_run',
                 help="Perform a trial run with no changes made")
    p.add_option("--shell-mode", "-s", action="store_true",
                 default=False, dest='shell_mode',
                 help="Run commands without Zenity support")

    options, arguments = p.parse_args()

    MountSmbShares(verbose=options.verbose,
                   filename=options.file,
                   dry_run=options.dry_run,
                   shell_mode=options.shell_mode).run()
    sys.exit(0)

if __name__ == '__main__':
    main()
