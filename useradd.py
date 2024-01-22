#!/usr/bin/env python3
"""
add user to LAN

input line:
    login:password:long_name:OU

"""

from gybon import Bakalari, asci
import argparse
import random
import sys
import os

CMD = {'sambatool':'/usr/bin/samba-tool',
    'edquota':'/usr/sbin/edquota',
    'usermod':'/usr/sbin/usermod',
    'adduser':'/usr/sbin/adduser',
    'userdel':'/usr/sbin/userdel',
    'passwd':'/usr/bin/passwd'}

PDC = 'hal.gybon'
PATH = {'profiles':'/home/samba/profiles',
         'home'   :'\\\\\\\\hal\\\\home',
         'profile':'\\\\\\\\hal\\\\profiles'}
COMPANY = "Gymnázium Boženy Němcové, Hradec Králové"

class Line():
    def __init__(self, line):
        try:
            # new format line
            self.login, self.passw, self.long_name, self.ou = line.strip().split(':')
        except:
            # old format line
            self.login, self.passw, self.long_name, self.mail_alias, self.ou = line.strip().split(':')
        self.prijmeni, self.jmeno = self.long_name.strip().split(' ', 1)

def update_baka_username(B, line):
    """ update username field in Baka DB """
    sql = "SELECT intern_kod, username FROM zaci  WHERE prijmeni=? AND jmeno=?"
    if not args.yes:
        print("=== update Baka DB ===")
        print(sql, (line.prijmeni, line.jmeno))
    row = B.select(sql, (line.prijmeni, line.jmeno)).fetchone()
    #print(row)
    if row and args.yes:
        B.update('zaci', {'username':line.login}, "intern_kod='{}'".format(row.intern_kod))

def update_NIS():
    """ update NIS """
    print("Update NIS...")
    cmd = ["cd /var/yp; make"]
    execute_commands(cmd)

def execute_commands(cmds):
    """ really execute commanads """
    for cmd in cmds:
        os.system(cmd)

def print_commands(cmds):
    """ print commands """
    print("=== Commands: ===\n")
    for cmd in cmds:
        print(cmd)
    print("\n=== For execute commands use '-y' ===")            

def delete_user(line):
    """ delete user """
    cmd = list()
    cmd += ["{} user delete {}".format(CMD['sambatool'], line.login)]
    cmd += ["rm -rf {}".format("/".join([PATH['profiles'], line.login]))]
    cmd += ["rm -rf {}".format("/".join([PATH['profiles'], line.login])+".*")]
    cmd += ["{} -r {}".format(CMD['userdel'], line.login)]
    return cmd

def add_user(line):
    """ add user """
    if not args.profesor:
        line.ou += ",OU=Students"
    cmd = list()
    cmd += ["{} -c \"{}\" -g users {}".format(CMD['adduser'], asci(line.long_name), line.login)]
    cmd += ["echo {} | {} --stdin {}".format(line.passw, CMD['passwd'], line.login)]
    cmd += ["{} user add {} {} --rfc2307-from-nss --gecos '{}' --home-directory={} --home-drive=G: --profile-path={} --given-name='{}' --surname='{}' --mail-address='{}' --company='{}' --userou=OU={}".format(CMD['sambatool'], line.login, line.passw, asci(line.long_name), "\\\\".join([PATH['home'], line.login]), "\\\\".join([PATH['profile'], line.login]), asci(line.jmeno), asci(line.prijmeni), line.login+'@gybon.cz', COMPANY, line.ou)]
    if args.profesor:
        cmd += ["{} -G profs {}".format(CMD['usermod'], line.login)]
        cmd += ["{} group addmembers \"Gybon Teachers\" {}".format(CMD['sambatool'], line.login)]
        cmd += ["/root/bin/set_quota_profs.sh {} set".format(line.login)]
    return cmd

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Make file for import users to Gybon LAN")
    parser.add_argument("-d", "--delete", action="store_true", help="delete users")
    parser.add_argument("-y", "--yes", action="store_true", help="make changes -- yes to all")
    parser.add_argument("-p", "--profesor", action="store_true", help="profesor")
    args = parser.parse_args()

    B = Bakalari()
    for f_line in sys.stdin:
        if f_line[:1] == "#":
            continue
        line = Line(f_line)
        if args.delete:
            cmd = delete_user(line)
        else:                
            cmd = add_user(line)
        if args.yes:
            execute_commands(cmd)
        else:
            print_commands(cmd)
        if not args.delete and not args.profesor:
            update_baka_username(B, line)
    if args.yes:
        update_NIS()
