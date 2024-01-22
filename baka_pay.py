#!/usr/bin/env python3
"""
mail pay notice - platební modul Bakaláři
"""

from gybon import Bakalari, Mail 
import argparse
from rich.console import Console

MSG_REMINDER = """Dobrý den,

evidujeme nazaplacenou částku ve výši {} Kč na účet školy. Prosíme, uhraďte částku co nejdříve. Informace o platbě (platební symboly) včetně QR kódu jsou přiravené v IS Bakaláři na adrese https://bakalari.gybon.cz.

Nápovědu, kde nalézt platební modul a připravenou platbu nalezete v PDF souboru:
http://www.gybon.cz/download/ruzne/ruzne/baka_platba.pdf

Děkujeme

--
Gymnázium Boženy Němcové
"""
MSG_INFO = """Dobrý den,

v IS Bakaláři na webové adrese  https://bakalari.gybon.cz je připravená platba za školní akci ve výši {} Kč. Informace o platbě (platební symboly) včetně QR kódu  naleznete v platebním modulu v IS Bakaláři.

Nápovědu, kde nalézt platební modul a připravenou platbu nalezete v PDF souboru:
http://www.gybon.cz/download/ruzne/ruzne/baka_platba.pdf

Děkujeme

--
Gymnázium Boženy Němcové
"""

MSG = {'reminder':MSG_REMINDER, 'info':MSG_INFO}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Poslat mail ZZ ohledně platby založené v platebním modulu v BAKA")
    parser.add_argument("-t", "--typ", help="typ hlášení {}".format(list(MSG.keys())), required=True)
    parser.add_argument("-f", "--file_", help="soubor csv z platebního modulu BAKA", required=True)
    parser.add_argument("-u", "--user", help="příjmení - vybrat konkrétního studenta")
    parser.add_argument("-s", "--send", action='store_true', help="Really send mail!!")
    parser.add_argument("-m", "--mail", action='store_true', help="připravit mail")
    parser.add_argument("-d", "--debug", action='store_true', help="poslat testovací mail")
    args = parser.parse_args()

    in_file = args.file_
    B = Bakalari()
    f = open(in_file, encoding="windows-1250")
    i_line = 0
    
    for line in f:
        i_line += 1
        item = line.strip().split(';')
        if i_line == 1:
            date = item[0]
        elif i_line == 2:
            subj = item[0]
        elif i_line == 3 or 'Celkem' in item[0] or 'Zpracov' in item[0]:
            continue
        else:
            if len(item[0].split(' ')) > 3:
                prijmeni, jm1, jm2, trida = item[0].split(' ')
                jmeno = jm1+' '+jm2
            else:
                prijmeni, jmeno, trida = item[0].split(' ')
            if args.user and args.user not in prijmeni:
                continue
            predpis = item[4] if args.typ == 'reminder' else item[3]
            #dluh = item[6]
            s = B.student(prijmeni=prijmeni, jmeno=jmeno)
            if s:
                try:
                    print("{} - {:25} předpis: {} --> {}".format(args.typ, " ".join([prijmeni, jmeno]), predpis, s.zz_email[0]))     
                except:
                    pass
            if args.mail:
                mail_to =  'test' if args.debug else 'zz'
                s.mail(MSG[args.typ].format(predpis), mail_from='bakalari@gybon.cz', mail_to=mail_to, mail_subj=subj, send=args.send)
    f.close()            
