#!/usr/bin/env python3
"""
make file for import LAN users
"""
from gybon import Bakalari, asci
import argparse
import random

def check_username(username):
    """ check if username exist """
    pass

def get_random_password(jmeno):
    """ random password """
    c = ['*', '.', '_', '!']
    return asci(jmeno.strip()[:3])+str(random.randint(100000, 999999))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Make file for import users to Gybon LAN")
    parser.add_argument("-t","--trida", help="all students from class")
    args = parser.parse_args()

    if not args.trida:
        print("no arguments!")
        exit()

    B = Bakalari()
    trida = B.select("select * from tridy where zkratka='{}'".format(args.trida)).fetchone()
    if trida == None:
        print("Třída neexistuje!")
        exit()
    rows_student = B.select("select intern_kod, prijmeni, jmeno, trida from zaci where trida=?",(args.trida))
    print("### trida: {} ###".format(args.trida))
    no,paralelka = args.trida.split('.')
    ou = str(trida.NASTUP)+"_"+paralelka+str(trida.STUD_DELKA)
    for student in rows_student:
        login = ".".join([asci(student.jmeno.strip().lower()), asci(student.prijmeni.strip().lower())])
        long_name = " ".join([student.prijmeni.strip(), student.jmeno.strip()]) 
        password = get_random_password(student.jmeno)
        user_line = ":".join([login, password, long_name, ou])
        print(user_line)
