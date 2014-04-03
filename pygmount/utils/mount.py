#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import datetime
import sys
import os
import os.path
import subprocess
import time
import apt
import logging
from apt.cache import LockFailedException
from PyZenity import Question, GetText, InfoMessage, ErrorMessage, Progress
from pygmount.utils.utils import get_sudo_username, read_config, get_home_dir

FILE_RC = '.pygmount.rc'


class MountSmbShares(object):
    """
    Classe di utilità per gestire il processo di montaggio di cartelle di rete
    condivise da server samba/windows.
    """

    def __init__(self, verbose=False, file=None,
                 dry_run=False, shell_mode=False):
        self.verbose = verbose
        self.file = file
        self.dry_run = dry_run
        self.shell_mode = shell_mode
        self.pkgs_required = ['smbfs']
        self.samba_shares = []
        self.sudo_env, self.host_username = get_sudo_username()
        self.cmd_mount = ("mount -t cifs //%(hostname)s/%(share)s "
                          "%(mountpoint)s"
                          " -o username=\"%(domain_username)s\""
                          ",uid=%(host_username)s"
                          ",password=\"%(domain_password)s\"")
        self.username = (self.host_username if self.host_username
                         else os.environ['USER'])
        self.cmd_umount = "umount %(mountpoint)s"
        self.msg_error = "Impossibile collegare le unità di rete [%s]."
        self.home_dir = get_home_dir()
        logging.basicConfig(
            filename='{}{}/.pygmount.log'.format(self.home_dir, self.username),
            filemode='a', level=logging.INFO)

    def requirements(self):
        """
        Verifica che tutti i pacchetti apt necessari al "funzionamento" della
        classe siano installati. Se cosi' non fosse li installa.
        """
        cache = apt.cache.Cache()
        for pkg in self.pkgs_required:
            try:
                pkg = cache[pkg]
                if not pkg.is_installed:
                    try:
                        pkg.mark_install()
                        cache.commit()
                    except LockFailedException as lfe:
                        logging.error(
                            'Errore "{}" probabilmente l\'utente {} non ha i '
                            'diritti di amministratore'.format(lfe,
                                                               self.username))
                        raise lfe
                    except Exception as e:
                        logging.error('Errore non classificato "{}"'.format(e))
                    raise e
            except KeyError as ke:
                logging.error('Il pacchetto "{}" non e\' presente in questa'
                              ' distribuzione'.format(pkg))


    def set_shares(self):
        """
        Setta la variabile membro 'self.samba_shares' il quale e' una lista
        di dizionari con i dati da passare ai comandi di "umount" e "mount".
        I vari dizionari sono popolati o da un file ~/.pygmount.rc e da un
        file passato dall'utente.
        """
        if self.file is None:
            self.file = os.path.expanduser('~%s/%s' % (self.host_username,
                                                       FILE_RC))
        if not os.path.exists(self.file):
            error_msg = (u"Impossibile trovare il file di configurazione "
                         u"'%s'.\nLe unità di rete non saranno collegate." % (
                             FILE_RC.lstrip('.')))
            if not self.shell_mode:
                ErrorMessage(error_msg)
            logging.error(error_msg)
            sys.exit(5)
        if self.verbose:
            logging.warning("File RC utilizzato: %s", self.file)
        self.samba_shares = read_config(self.file)

    def run(self):
        """
        Esegue il montaggio delle varie condivisioni chiedendo all'utente
        username e password di dominio.
        """
        logging.info('start run with "{}" at {}'.format(
            self.username, datetime.datetime.now()))
        progress = Progress(text="Controllo requisiti software...",
                            pulsate=True, auto_close=True)
        progress(1)
        try:
            self.requirements()
        except LockFailedException as lfe:
            ErrorMessage('Errore "{}" probabilmente l\'utente {} non ha i'
                         ' diritti di amministratore'.format(lfe,
                                                             self.username))
            sys.exit(20)
        except Exception as e:
            ErrorMessage("Si e' verificato un errore generico: {}".format(e))
            sys.exit(21)
        progress(100)

        self.set_shares()
        # richiesta username del dominio
        insert_msg = "Inserisci l'utente del Dominio/Posta Elettronica"
        default_username = (self.host_username if self.host_username
                            else os.environ['USER'])
        self.domain_username = GetText(text=insert_msg,
                                       entry_text=self.username)

        if self.domain_username is None or len(self.domain_username) == 0:
            error_msg = "Inserimento di un username di dominio vuoto"
            ErrorMessage(self.msg_error % error_msg)
            sys.exit(2)

        # richiesta della password di dominio
        insert_msg = u"Inserisci la password del Dominio/Posta Elettronica"
        self.domain_password = GetText(text=insert_msg,
                                       entry_text='password',
                                       password=True)

        if self.domain_password is None or len(self.domain_password) == 0:
            error_msg = u"Inserimento di una password di dominio vuota"
            ErrorMessage(self.msg_error % error_msg)
            sys.exit(3)

        progress_msg = u"Collegamento unità di rete in corso..."
        progress = Progress(text=progress_msg,
                            pulsate=True,
                            auto_close=True)
        progress(1)
        # ciclo per montare tutte le condivisioni
        result = []
        for share in self.samba_shares:
            # print("#######")
            # print(share)
            if 'mountpoint' not in share.keys():
                # creazione stringa che rappresente il mount-point locale
                mountpoint = os.path.expanduser(
                    '~%s/%s/%s' % (self.host_username,
                                   share['hostname'],
                                   share['share']))
                share.update({'mountpoint': mountpoint})
            elif not share['mountpoint'].startswith('/'):
                mountpoint = os.path.expanduser(
                    '~%s/%s' % (self.host_username, share['mountpoint']))
                share.update({'mountpoint': mountpoint})

            share.update({
                'host_username': self.host_username,
                'domain_username': share.get(
                    'username', self.domain_username),
                'domain_password': share.get(
                    'password', self.domain_password)})

            # controllo che il mount-point locale esista altrimenti non
            # viene creato
            if not os.path.exists(share['mountpoint']):
                if self.verbose:
                    logging.warning('Mountpoint "%s" not exist.' %
                                    share['mountpoint'])
                if not self.dry_run:
                    os.makedirs(share['mountpoint'])

            # smonto la condivisione prima di rimontarla
            umont_cmd = self.cmd_umount % share
            if self.verbose:
                logging.warning("Umount command: %s" % umont_cmd)
            if not self.dry_run:
                umount_p = subprocess.Popen(umont_cmd,
                                            shell=True)
                returncode = umount_p.wait()
                time.sleep(2)

            mount_cmd = self.cmd_mount % share
            if self.verbose:
                placeholder = ",password="
                logging.warning("Mount command: %s%s" % (mount_cmd.split(
                    placeholder)[0], placeholder + "******\""))

            # print(mount_cmd)
            # print("#######")
            if not self.dry_run:
                # montaggio della condivisione
                p_mnt = subprocess.Popen(mount_cmd, shell=True,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
                returncode = p_mnt.wait()
                result.append({'share': share['share'],
                               'returncode': returncode,
                               'stdout': p_mnt.stdout.read(),
                               'stderr': p_mnt.stderr.read()})
        progress(100)
        if self.verbose:
            logging.warning("Risultati: %s" % result)




