#!/usr/bin/env python3
"""
Připraví soubory pro import absoventů do mysql
"""
import argparse
import dbf

dir_abs = "/opt/win/apps/bakalari/evid/absolv"

parser = argparse.ArgumentParser(description="Create import to mysql db skola")
parser.add_argument("-y","--year",help="maturitní rok")
args = parser.parse_args()

if args.year == None:
    print("Není zadán rok! - konec")
    exit()

# -- dbf file --
dbf_file = "/".join([dir_abs, "".join(["abs", args.year]), "ZAL_Z"+args.year[2:4]+".dbf"])
t = dbf.Table(dbf_file)
t.open()
for r in t:
    #print(r)
    #exit()
    s_index = 1 if r['trida'][0:1] == "S" else 0
    stdel = r['trida'][s_index:s_index+1]
    para = r['trida'][s_index+2:s_index+3]
    print(",{},{},{},{},{},{},{}".format(r['prijmeni'].strip(), r['jmeno'].strip(), r['pohlavi'], args.year, stdel, para, r['e_mail']))
