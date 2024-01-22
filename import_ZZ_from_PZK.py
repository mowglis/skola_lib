#!/usr/bin/env python3
"""
import ZZ z PZK
"""
import sys
sys.path.insert(1, '/home/rusek/skola/lib')
from gybon import Bakalari, Pzk_DB, ZZ
from rich import print
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zápis položek ZZ do db Bakaláři z PZK")
    parser.add_argument("-r","--rok", help="evidence studenta od roku - povinný parametr")
    parser.add_argument("-t","--trida", help="zadej třídu - povinný parametr")
    parser.add_argument("-w","--wr", action='store_true', help="provede se zápis do db baka")
    args = parser.parse_args()

    baka = Bakalari()
    pzk = Pzk_DB()

    if args.trida:
        print("Studenti třídy: {}".format(args.trida))
        for student in baka.trida(args.trida):
            if len(student.zz) == 0:
                uchazec = pzk.uchazec(prijmeni=student.prijmeni, jmeno=student.jmeno)
                st = baka.get_ZZ(prijmeni=uchazec.zast_prijmeni, jmeno=uchazec.zast_jmeno)
                print("\n{} {} 'ZZ' -> {}".format(student.prijmeni, student.jmeno, st))
                if st is None:
                    new_zz = ZZ.from_PZK(uchazec, student.i_kod)
                    if args.wr:
                        baka.add_ZZ(new_zz)
                #break
            else:
                print("\n{} {} -> {}".format(student.prijmeni, student.jmeno, student.zz))
                for zz in student.zz:
                    st = baka.get_ZZ(prijmeni=zz.prijmeni, jmeno=zz.jmeno)
                    print("{} {} -> {}".format(zz.prijmeni, zz.jmeno, st))
    else:
        parser.print_help()