#!/usr/bin/env python3
"""
Nastaví EČ (evidenční číslo) studentů
"""
import argparse
import pyodbc as ms

def baka_modify(kod, ev_cislo):
    """ modify baka db """
    sql = "UPDATE zaci SET ev_cislo='{}' WHERE intern_kod='{}'".format(ev_cislo, kod)
    cur_wr.execute(sql)

def baka_search(year=None, name=None):
    """ search student in baka DB """
    #print(year)
    if year:
    	sql = "SELECT prijmeni, jmeno, trida, evid_od, ev_cislo, intern_kod FROM zaci WHERE YEAR(evid_od) = {} ORDER by ev_cislo DESC , prijmeni,jmeno".format(year)
    elif name:
    	sql = "SELECT prijmeni, jmeno, trida, evid_od, ev_cislo, intern_kod FROM zaci WHERE prijmeni LIKE '{}%' ORDER by prijmeni,jmeno".format(name)
    else:
        exit()
    cur.execute(sql)
    return cur

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nastaví EČ (evidenční číslo) u studentů")
    parser.add_argument("-y","--year",help="year - ročník")
    parser.add_argument("-w","--write", action='store_true', help="zapíše EV čísla do db")
    args = parser.parse_args()

    # connect -- SQL Bakalari --
    baka = ms.connect("Driver={ODBC Driver 17 for SQL Server};Server=bakalari-w2012;UID=sa;PWD=Admin789;Database=bakalari;")
    cur = baka.cursor()
    cur_wr = baka.cursor()

    # --- utf8 - ascii ---
    intab = "áčďéěíľňóřšťúůýžöü"
    outab = "acdeeilnorstuuyzou"
    asci = str.maketrans(intab, outab)

    i = 0
    empty_val = 7*'-'
    if args.year:
        print("Rok nástupu: {}".format(args.year))
        res = baka_search(year=args.year).fetchall()
        for prijmeni, jmeno, trida, evid_od, ev_cislo, i_kod in res:
            i += 1
            ev_c = "{}{:03}".format(args.year,i) if ev_cislo.strip() == '' else empty_val
            ev_cislo = ev_cislo.strip() if ev_cislo.strip() != '' else empty_val

            print("{} {:<25} kód:{} evid_od:{} ev_cislo:{} >> {}".format(trida.strip(), " ".join([prijmeni.strip(), jmeno.strip()]), i_kod, evid_od, ev_cislo, ev_c), end="")
            if args.write and ev_c != empty_val:
                baka_modify(i_kod, ev_c) 
                print("...write")
            else:
                print()
    else:
        print("Není zadán rok nebo jméno studenta!")

    baka.commit()
