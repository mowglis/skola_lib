#!/usr/bin/env python3
"""
mail passwrd to users
input:
    - template - [gsuite, office365]
    - csv file: name, login, passw
"""
import fileinput, os
import argparse
import sys
from gybon import Mail, Bakalari
from rich.console import Console
from rich.table import Table
from rich import print
from rich.live import Live

SENDER = 'noreply@gybon.cz'
TEMPLATE = ['office365', 'gsuite', 'gybon'];
SUBJ =  {
  'office365':"Účet Office 365 pro studenty/učitele Gybonu",
  'gsuite': "Účet Google Workspace pro studenty/učitele Gybonu",
  'gybon': "Účet v  LAN Gybon"
}
MESSAGE = {
'office365':"Dobrý den,\nbyl vám zřízen školní účet pro využití cloudové aplikace Office 365.\nPro aktivaci Vašeho účtu využijte odkaz https://www.office.com -- zde budete vyzváni k zadání prvotního hesla a následně ke změně tohoto prvotního hesla.\n\nVáš přihlašovací účet: {}\nVaše prvotní heslo: {}\n\nIT Gybon",
'gsuite':"Dobrý den,\nbyl vám zřízen účet pro využití cloudové aplikace Google Workspace.\nPro přihlášení do cloudových služeb Google využijte nový školní Google účet.\n\nVáš školní Google účet: {}\nVaše prvotní heslo: {}\n\nhttps://www.google.cz/apps/intl/cs/edu/sell.html\nIT Gybon",
'gybon':"Dobrý den,\nbyl vám zřízen účet do školní LAN sítě. \n\nlogin: {}\nHeslo: {}\n\nIT Gybon"
}

def get_items(template, line):
    """ items: name, account, mail, passw """
    if template == 'office365':
        name, account, passw, etc = line.strip().split(',',3)
        if not '@' in account:
            return None, None, None, None
        login, domain = account.split('@')
        mail = '@'.join([login, 'gybon.cz'])
    elif template == 'gsuite':        
        f_name, l_name, account, passw, etc = line.strip().split(',',4)
        name = f_name+" "+l_name
        if f_name == 'First Name [Required]':
            return None, None, None, None
        login, domain = account.split('@')
        mail = '@'.join([login, 'gybon.cz'])
    elif template == 'gybon':
        account, passw, name, rest = line.strip().split(':', 3)
        try:
            #mail = B.ucitel(login=account).email if args.ucitel else B.student(login=account).email
            mail = B.ucitel(login=account).email if args.ucitel else  '@'.join([account, 'gybon.cz'])
        except:
            mail = ''

    if args.debug:
        mail = 'rusek@gybon.cz'

    if not args.login or (args.login and (args.login in account)):
        return name, account, mail, passw              
    else:
        return None

def mail_message(template, items):
    """ mail messsage """
    if items == None:
        return
    name, login, mail_to, passw = items
    if name == None:
        return
    login_gybon = login.split('@')[0]        
    student = B.student(login=login_gybon)
    if student:
        t.add_row(name, "{} ({})".format(login, passw), mail_to)
        if args.yes:
            mail_to = 'gybon' if not args.debug else 'test'
            #mail_to = 'private' if not args.debug else 'test'
            student.mail(MESSAGE[template].format(login, passw), mail_to=mail_to, mail_subj=SUBJ[template], send=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mail to users")
    parser.add_argument("-t", "--template", help="template {}".format(TEMPLATE))
    parser.add_argument("-f", "--file", help="csv file")
    parser.add_argument("-l", "--login", help="login - username")
    parser.add_argument("-d", "--debug", help="debug  -- sent mail to rusek@gybon.cz", action="store_true")
    parser.add_argument("-u", "--ucitel", action='store_true', help="Učitelé")
    parser.add_argument("-y", "--yes", help="send!", action="store_true")
    args = parser.parse_args()

    if not len(sys.argv) > 1:
        parser.print_help()
        exit()

    if args.template not in TEMPLATE:
        print("ERROR - template not in list of templates {}".format(TEMPLATE))
        exit()
    f = open(args.file)
    if not args.yes:
        print("Messages not really sending - use option: -y")
    else:
        mail = Mail()
    
    B = Bakalari()
    c = Console()
    t = Table(highlight=False, title="Send password info - {}".format(args.template), title_justify="left")
    t.add_column("Student")
    t.add_column("login/password")
    t.add_column("Destination")
    with Live(t, auto_refresh=False) as live:
        for line in f:
            if line[0:1] == "#":
                continue
            mail_message(args.template, get_items(args.template, line))
            live.update(t)
    f.close()
