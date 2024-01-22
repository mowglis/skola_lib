#!/usr/bin/env python3
"""
get data from AD
"""
import ldap3
import argparse, sys
import random
import string
from gybon import It_DB, Bakalari
from datetime import datetime

# --- utf8 - ascii ---
intab = "áčďéěíľňóřšťúůýžöü"
outab = "acdeeilnorstuuyzou"
asci = str.maketrans(intab, outab)

templates = {
  'office365': "Uživatelské jméno,Jméno,Příjmení,Zobrazované jméno,Funkce,Oddělení,Číslo kanceláře,Telefon do kanceláře,Mobilní telefon,Faxové číslo,Adresa,Město,Kraj,PSČ,Země či oblast", 
  'arcgis': "Jméno,Příjmení,E-mail,Uživatelské jméno,Role,Typ uživatele,Heslo",
  'gsuite': "First Name [Required], Last Name [Required], Email Address [Required], Password [Required], Password Hash Function [UPLOAD ONLY], Org Unit Path [Required], New Primary Email [UPLOAD ONLY], Recovery Email, Home Secondary Email, Work Secondary Email, Recovery Phone [MUST BE IN THE E.164 FORMAT], Work Phone, Home Phone, Mobile Phone, Work Address, Home Address, Employee ID, Employee Type, Employee Title, Manager Email, Department, Cost Center, Building ID, Floor Name, Floor Section, Change Password at Next Sign-In, New Status [UPLOAD ONLY]",
  'moodle':'username,course1,role1,group1'
} 

from_to = (2016, 2022)

get_pager = lambda x: x["pager"][0] if "pager" in x.keys() else "--------"
get_attrib = lambda x,attr: x['attributes'][attr]
get_current_classname = lambda x: '.'.join([str(int(datetime.now().year)-int(x[0:4])), x[5]])


def get_password(login):
    """ get pass from db """
    sql = "SELECT password FROM people WHERE login='{}'".format(login)
    try:
        return db.execute(sql).fetchone()['password']
    except:
        return ''

def get_baka_items(login):
    """ get from Baka """
    if args.ucitel:
        s = baka.ucitel(login=login) 
        #s.list_items()
        return s.prijmeni, s.jmeno, s.item(89)
    else:
        s = baka.student(login=login)
        return s.prijmeni, s.jmeno, s.email
    
def random_password():
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    size = random.randint(8, 12)
    return ''.join(random.choice(chars) for x in range(size))

def get_ad_items(ad, trida=None):
    """ get items from AD response """
    sam_account = get_attrib(ad, 'sAMAccountName')
 
    """
    try:
        jm, pr = get_attrib(ad,'name').split(' ',1)
    except ValueError:
        pr = get_attrib(ad,'name')
        jm = ''
    try:        
        mail = get_attrib(ad, 'mail') if type(get_attrib(ad, 'mail')) is str else '' 
    except KeyError:
        mail = ''
    """
    try:
        pr, jm, mail = get_baka_items(sam_account)
    except:
        return

    if args.template=='office365':
        login = '@'.join((sam_account, args.domain))
        cls = '' if args.ucitel else trida
        fce = 'Teacher' if args.ucitel else 'Student'
        items = [login, jm, pr, ' '.join((jm, pr)), fce, cls, '', '', '', '', '', '', '', '', 'Czech republic']
        return ','.join(items)
    
    elif args.template == 'gsuite':
        ou = "/".join(['/Students', trida])  if not args.ucitel else '/Teachers' 
        department = trida if not args.ucitel else ''
        password = "****" if args.nopass else get_password(sam_account)
        #true_false = "FALSE" if args.nopass else "TRUE"
        #new_primary_mail = '@'.join((sam_account, 'gybon.cz'))
        new_primary_mail = ''
        true_false = "TRUE"
        items = [jm, pr, '@'.join((sam_account, args.domain)), password, '', ou, new_primary_mail, mail,'', '', '', '', '', '' ,'' ,'','','','','',department,'','','','',true_false,'']
        return ','.join(items)
    
    elif args.template == 'arcgis':
        return ",".join((jm, pr, mail, sam_account, 'Uživatel', 'GIS Professional Advanced', 'TajneHes10'))
    
    elif args.template == 'moodle':
        if args.ucitel:
            return ",".join((sam_account, args.moodle,'Teacher')) 
        else:
            return ",".join((sam_account, args.moodle, 'Student', get_current_classname(args.cls))) 

def search_ad(sam=None, ou=''):
    """ search AD for SAMAccountName """
    _filter = '(objectclass=person)'
    _base =  "ou=Students,dc=local,dc=gybon" if not args.ucitel else "ou=Teachers,dc=local,dc=gybon"
    s_base = "ou={},{}".format(ou, _base) if ou else _base
    s_filter = "(&{}(sAMAccountname={}))".format(_filter, sam) if sam else _filter
    #print("Search filter: {} {}".format(s_base, s_filter))
    if c.search(
           search_base=s_base,
           search_filter=s_filter,
           attributes=['sAMAccountName','name','pager','cn','givenName','mail']):
        return c.response

if "__main__" == __name__:
    parser = argparse.ArgumentParser(description="Get data from AD")
    parser.add_argument("-c","--cls", help="list student class - třída (2018_A6)")
    parser.add_argument("-l","--login", help="login name")
    parser.add_argument('-t','--template', required=True, help="template - šablona pro výstup {}".format(list(templates.keys())))
    parser.add_argument('-a','--all', action='store_true', help="all classes")
    parser.add_argument('-u','--ucitel', action='store_true', help="all teachers")
    parser.add_argument('-m','--moodle', help="moodle course")
    parser.add_argument('-d','--domain', help="domain name", required=True)
    parser.add_argument('-n','--nopass', help="no password", action='store_true')
    parser.add_argument('-w','--write', help="write file", action='store_true')
    args = parser.parse_args()
    
    if not len(sys.argv) > 1:
        parser.print_help()
        exit()

    # connect -- AD - ldap --
    ad_server = ldap3.Server('hal.gybon')
    c = ldap3.Connection(ad_server, user='root@local.gybon', password='Edunix456', auto_bind=True)
    db = It_DB()
    baka = Bakalari()

    if args.template and not args.template in templates:
        parser.print_help()
        exit()

    if args.login:
        print(templates[args.template])
        try:
            print(get_ad_items(search_ad(sam=args.login)[0]))
        except :
            pass
    
    elif args.cls:
        print(templates[args.template])
        for entry in search_ad(ou=args.cls):
            try:
                print(get_ad_items(entry, trida=args.cls))
            except:
                continue
    
    elif args.all:
        tridy = [ "_".join((str(rok),str(trida))) for rok in range(from_to[0], from_to[1]) for trida in ['A6', 'B6', 'C6']]
        for trida in tridy:
            print("třída: {}".format(trida))
            
            if args.write:
                f = open('gsuite_'+trida+'.csv','w')
                f.write(templates[args.template]+'\n')
                            
            for entry in search_ad(ou=trida):
                try:
                    if args.write:
                        f.write(get_ad_items(entry, trida=trida)+'\n')     
                    else:
                        print(get_ad_items(entry, trida=trida))
                except:
                    continue
            if args.write:
                f.close()

    elif args.ucitel:
        print(templates[args.template])
        for entry in search_ad():
            try:
                print(get_ad_items(entry))        
            except:
                continue
    
    else:
        print(search_ad())
