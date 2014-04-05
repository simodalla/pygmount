#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import tempfile
import subprocess

if __name__ == '__main__':
    tmpdir = tempfile.mkdtemp()
    tmpsudoers = "%s/sudoers" % tmpdir
    print(tmpdir)
    shutil.copy('/etc/sudoers', tmpsudoers)
    print(os.listdir(tmpdir))
    #print "visudo -cf %s" % tmpsudoers

    mounters_enty = ""

    f = open(tmpsudoers, 'r')

    if f.read().find(mounters_enty) == -1:
        f = open(tmpsudoers, 'a')
        f.write('\n%s\n' % mounters_enty)
    f.close()

    print(open(tmpsudoers, 'r').read())

    if subprocess.call("visudo -cf %s" % tmpsudoers, shell=True) == 0:
        shutil.move(tmpsudoers, '/etc/sudoers')

    shutil.rmtree(tmpdir)
    sys.exit(0)
