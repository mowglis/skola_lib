#!/usr/bin/env python3
"""
Nastaví osobní číslo učitelů
"""
import argparse
#import pymssql as ms
import pyodbc as ms

def baka_modify(kod, osob_cislo):
    """ modify baka db """
    sql = "UPDATE ucitele SET osob_cislo='{}' WHERE intern_kod='{}'".format(osob_cislo, kod)
    #print(sql)
    cur_wr.execute(sql)

def baka_search():
    """ search in baka DB """
    sql = "SELECT prijmeni, jmeno, osob_cislo, dat_nastup, intern_kod FROM ucitele WHERE deleted_rc=0 ORDER by dat_nastup, prijmeni, jmeno"
    cur.execute(sql)
    return cur

parser = argparse.ArgumentParser(description="Nastaví osobní číslo u učitelů")
parser.add_argument("-w","--wr", action='store_true', help="zapíše OC čísla do db")
args = parser.parse_args()

# connect -- SQL Bakalari --
#baka = ms.connect("bakalari-w2012","sa","Admin789","bakalari")
baka = ms.connect("Driver={ODBC Driver 17 for SQL Server};Server=bakalari-w2012;UID=sa;PWD=Admin789;Database=bakalari;")
cur = baka.cursor()
cur_wr = baka.cursor()

# --- utf8 - ascii ---
intab = "áčďéěíľňóřšťúůýžöü"
outab = "acdeeilnorstuuyzou"
asci = str.maketrans(intab, outab)

i = 0
res = baka_search().fetchall()
#print(res)
pred_rok = 0
for prijmeni, jmeno, osob_c, datn, i_kod in sorted(res, key=lambda x:x[3].timetuple().tm_year if x[3] else 0):
  if not datn:
    continue
  if datn and pred_rok != datn.timetuple().tm_year:
    i = 0
    pred_rok = datn.timetuple().tm_year
  i += 1
#  print(prijmeni.strip(), jmeno.strip(), osob_c, datn, i_kod.strip(),end='')
#  print(prijmeni.strip(), jmeno.strip(), end='' )
  oc =  "ok" if osob_c.strip()!='' else "{}{:02}".format(datn.timetuple().tm_year,i)
  
  print("{:<25} {:6} -- {}".format(" ".join([prijmeni.strip(), jmeno.strip()]), osob_c.strip(), oc), end="")
  if args.wr and oc != 'ok':
    baka_modify(i_kod, oc) 
    print("...write")
  else:
    print()

baka.commit()
