#!/usr/bin/env python3
"""
Výpis/nastavení hodnoty pager do AD
"""
import ldap3
import argparse
import pyodbc as ms
from termcolor import colored

get_pager = lambda x: x["pager"] if type(x['pager']) is not list  else "--------"
format_chip = lambda x: " ".join([x[0:2], x[2:4], x[4:6], x[6:8]])

def print_user(attrib, cip=""):
    """ print user attribs """
    #print(attrib)
    user = "{} ({})".format(attrib['sAMAccountName'], attrib['name'])
    pager =  get_pager(attrib)
    if cip:
        res = colored('ok','green') if cip.upper() == pager.upper() else colored('** error **','red')
    else:
        res = ""
    print("AD: {:50} [{}]  {}".format(user, format_chip(pager), res))

def modify_pager(dn, pager):
    """ modify pager """
    modify = {"pager":[(ldap3.MODIFY_REPLACE, [pager])]}
    print("Set new pager '{}' for DN '{}'".format(pager,dn))
    c.modify(dn, modify)
    #print(c.result)	

def search_baka(user=None, trida=None):
    """ search student/teacher in baka DB """
    sql = {"zaci":"SELECT prijmeni, jmeno, isic_cip, username FROM zaci ", "ucitele":"SELECT prijmeni, jmeno, isic_cip, '###' FROM ucitele "}
    for table in ['zaci', 'ucitele']:
        if user != None:
            name = user.split(" ")
            sql[table] += "WHERE prijmeni='{}' ".format(name[0])
            sql[table] += "AND jmeno='{}'".format(name[1]) if len(name)>1 else ""
        if trida != None:
            sql[table] += "WHERE trida='{}' ".format(trida)	
        cur.execute(sql[table])
        if cur.rowcount == -1:
            break
    return cur

def search_ad(sam=None):
    """ search AD for SAMAccountName """
    _filter = '(objectclass=person)'
    s_filter = "(&{}(sAMAccountname={}))".format(_filter, sam) if sam else _filter
    for ou in ['Students', 'Teachers']:
        s_base = "ou={},dc=local,dc=gybon".format(ou)
   #    print("{} {}".format(s_base, s_filter))
        if c.search(
                search_base=s_base,
                search_filter=s_filter,
                attributes=['sAMAccountName','name','pager','cn','givenName']):
            break                
    return c.response
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List/update ISIC code from DB Bakalari to AD value pager")
    parser.add_argument("-s","--sam",help="sAMAccountName in AD = win/unix user login name")
    parser.add_argument("-p","--pager",help="set new Pager (=ISIC code) for 'sam' account" )
    parser.add_argument("-n","--name",help="student name in DB  Bakalari")
    parser.add_argument("-w","--wr", action='store_true', help="write ISIC code to AD pager field")
    parser.add_argument("-a","--all", action='store_true', help="list all students in DB Bakalari and check to AD")
    parser.add_argument("-t","--trida", help="list student class")
    args = parser.parse_args()

    # connect -- AD - ldap --
    ad_server = ldap3.Server('hal.gybon')
    c = ldap3.Connection(ad_server, user='root@local.gybon', password='Edunix456', auto_bind=True)

    # connect -- SQL Bakalari --
    #baka = ms.connect("bakalari-w2012","sa","Admin789","bakalari")
    baka = ms.connect("Driver={ODBC Driver 17 for SQL Server};Server=bakalari-w2012;UID=sa;PWD=Admin789;Database=bakalari;")
    cur = baka.cursor()

    # --- utf8 - ascii ---
    intab = "áčďéěíľňóřšťúůýžöü"
    outab = "acdeeilnorstuuyzou"
    asci = str.maketrans(intab, outab)

    if args.name or args.all or args.trida:
        print("Search name: {}".format(args.name))
        for prijmeni,jmeno, cip, username in search_baka(args.name, args.trida):
            cip = cip.strip()
            username = username.strip()
            _cip_ = "".join([cip[6:8], cip[4:6], cip[2:4], cip[0:2]])
            bb = "BAKA: {:25} [{}]".format(" ".join([prijmeni.strip(), jmeno.strip()]), format_chip(_cip_))  
            print("{} -- ".format(bb), end="")
            if username == "###":
                samaccount = prijmeni.strip()
            else:            
                samaccount = jmeno[:3]+prijmeni[:4] if username == "" else username
                
            samaccount = samaccount.lower().translate(asci)
            for entry in search_ad(sam=samaccount):
                print_user(entry['attributes'], _cip_)
                if get_pager(entry['attributes']) != _cip_ and args.wr:
                    modify_pager(entry['dn'], _cip_)

    elif args.sam:
        print("Search sAMAccountName: {}".format(args.sam))
        if args.pager:
            print("New pager: {}".format(args.pager))
        for entry in search_ad(sam=args.sam):
            print_user(entry['attributes'])
            if args.sam and args.pager:
                modify_pager(entry['dn'], args.pager)
    else:
        for entry in search_ad():
            print_user(entry['attributes'])

