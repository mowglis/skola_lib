#!/usr/bin/env python3
"""
mail baka pass to student/parents
"""
import ldap3
import argparse
import pyodbc as ms
import os
from termcolor import colored
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

message = "Dobrý den,\n\nVaše přihlašovací jméno do systému Bakaláři (https://bakalari.gybon.cz/bakaweb) je '{}' (text uvnitř apostrofů). Pro vstup zadejte heslo '{}' (text uvnitř apostrofů)\n\nPokud budete mít problémy  s přihlášením, vyzkoušejte reset hesla pomocí volby 'Zapomenuté heslo' na přihlašovací stránce systému Bakaláři.\n\n---\nIT Gybon"
subj = "Přístupové údaje do systému Bakaláři"
sender = 'it@gybon.cz'
smtp_auth = ('ru', 'mauglis')

def mail_message(login, passw, send_to):
    """ send mail """
    debug_mail = False
    for _to in send_to:
        if _to == '':
            continue
        if debug_mail:
            _to = 'mgli.orusek@gmail.com'
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = _to
        msg['Subject'] = subj
        msg.attach(MIMEText(message.format(login, passw), 'plain'))
        smtp_server = smtplib.SMTP('smtp.gybon.cz:587')
        smtp_server.starttls()
        smtp_server.login(smtp_auth[0], smtp_auth[1])
        smtp_server.sendmail(sender, _to, msg.as_string())
        smtp_server.quit()
        print("successsfly sent mail to {}".format(_to))
      
        #cmd = "echo \""+MESSAGE.format(login, passw)+"\" | mutt -s \""+SUBJ+"\" "+_to
        #print(cmd)
        #os.system(cmd)    

def search_baka(user=None, trida=None):
    """ search student/teacher in baka DB """
    sql = "SELECT zaci.prijmeni, zaci.jmeno, zaci.e_mail, zaci_zzd.e_mail  FROM zaci, zaci_zzr, zaci_zzd WHERE zaci.intern_kod=zaci_zzr.intern_kod AND zaci_zzr.id_zz=zaci_zzd.id "
    #sql = "SELECT prijmeni, jmeno, e_mail FROM zaci "
    if user != None:
        name = user.split(" ")
        sql += "AND zaci.prijmeni like '{}%' ".format(name[0])
        sql += "AND zaci.jmeno='{}'".format(name[1]) if len(name)>1 else ""
    if trida != None:
        sql += "AND trida='{}' ".format(trida)	
    #print(sql)        
    cur.execute(sql)
    ret = []
    st = []
    for prijmeni, jmeno, mail_z, mail_zz in cur:
        if prijmeni.strip() in st:
            st += [mail_zz.strip()]
        else:
            if len(st) > 0:
                ret += [st]
            st = [prijmeni.strip(), jmeno.strip(), mail_z.strip(), mail_zz.strip()]
        #print(st)            
    if len(st) > 0:
        ret += [st]
    if len(ret) == 0:
        print("Nenalezeno!")
    return ret

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send mail to student/parents with login/pass to IS Baka")
    parser.add_argument("-s","--student", action='store_true',help="send mail to student")
    parser.add_argument("-p","--parent", action='store_true',help="send pass to parent (ZZ)" )
    parser.add_argument("-n","--name", help="student name in DB  Bakalari")
    parser.add_argument("-m","--mail", action='store_true', help="send mail")
    parser.add_argument("-t","--trida", help="all students from class")
    parser.add_argument("-f","--file", help="file with auth info")
    args = parser.parse_args()

    # connect -- SQL Bakalari --
    #baka = ms.connect("bakalari-w2012","sa","Admin789","bakalari")
    baka = ms.connect("Driver={ODBC Driver 17 for SQL Server};Server=bakalari-w2012;UID=sa;PWD=Admin789;Database=bakalari;")
    cur = baka.cursor()

    # --- utf8 - ascii ---
    intab = "áčďéěíľňóřšťúůýžöü"
    outab = "acdeeilnorstuuyzou"
    asci = str.maketrans(intab, outab)

    if not args.name and not args.trida:
        print("not set params!")
        exit()

    if args.file:
        f = open(args.file)
        auth = []
        for line in f:
            if 'heslo' in line.lower():
                items = line.strip().split(' ')
                auth_line = [items[0].strip(), items[1].strip()]
                for i in range(2,len(items)):
                    if items[0][0:4] in items[i]:
                        auth_line += [items[i].strip()]
                    if items[i].strip().lower() == 'heslo':
                        auth_line += [items[i+1].strip()]
                        break
                auth += [auth_line]
                    
    print("Search - name: {} - trida: {}".format(args.name, args.trida))
    for student in search_baka(args.name, args.trida):
        prijmeni, jmeno, mail = student[0], student[1], student[2]
        zz = student[3:]
        print("student: {:26} - mail: {:35} ZZ: {}".format(" ".join((prijmeni,jmeno)), mail, zz))
        if args.parent or args.student:
            l = [ item for item in auth if item[0].lower().translate(asci) == prijmeni.lower().translate(asci)]
            #print(l)
            if len(l) > 0:
                login = l[0][2]
                passw = l[0][3]
            send_to = zz if args.parent else mail
            print("         -- login: {} passw: {} --> {}".format(login, passw, send_to))
            if args.mail:
                mail_message(login, passw, send_to)
            
                
