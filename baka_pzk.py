#!/usr/bin/env python3
"""
Položky z PZK do Baka

PZK.fields -> Baka.fields
=========================
tb_obec     misto
tb_psc      psc
tb_ulice    ulice
tb_cp       ulice_cp
tb_stat     = 203
puv_izo     izo_zs
misto_nar   misto_nar

Nastavení dat pro matriku:
==========================
ZAMERENI    - studijni obor 
PRISEL      - příchod do 1. ročníku (A)
ST_PRISL_K  - státní občanství - (3 - ČR)
SD_PLNENI   - plnění PŠD (4l - F, 6l- T)
ABSOLV_ZS   - abs. let na ZŠ (4l - 9, 6l - 7)
PUV_VZDEL   - předchozí vzdělání (4l - základní [3], 6l - bez [1]
PUV_PUSOB   - předchozí působiště (4l - z 9. roč [109], 6l - ze 7. roč. [107]
PRIHL_OD    - stejné jako EVID_OD - začátek evidence
ABSOLV_LET  - let na škole (podle akt. ročníku)

"""
import argparse
import pyodbc as ms
import pymysql as mysql

def baka_modify_pzk(kod, pzk):
    """ modify baka db - data from pzk """
    try:
        psc=" ".join([pzk['psc'][0:3], pzk['psc'][3:]])
        rc = "".join([pzk['rc'][0:6], pzk['rc'][7:]])
        sql = "UPDATE zaci SET tb_obec='{}', tb_psc='{}', tb_ulice='{}', tb_cp='{}', tb_stat='203', puv_izo='{}', misto_nar='{}', e_mail='{}', rodne_c='{}' WHERE intern_kod='{}'".format(pzk['misto'], psc, pzk['ulice'], pzk['ulice_cp'], pzk['izo_zs'], pzk['misto_nar'], pzk['e_mail0'],pzk['rc'], kod)
        print("SQL ({}): {}".format(args.wr, sql))
        if args.wr:
            cur_wr.execute(sql)
    except:
        print("*** Error - no record in PZK")

def baka_modify_matrika(kod, rok):
    """ modify baka -- matrika """
    datum_nastup = lambda r: '.'.join(['9','1',str(r)])
    matrika = {
        'zamereni':'SVP6',
        'prisel':'A',
        'st_prisl_k':3,
        'sd_plneni':1,
        'absolv_zs':7,
        'puv_vzdel':1,
        'puv_pusob':107,
        'prihl_od': datum_nastup(rok),
        'evid_od': datum_nastup(rok),
        'absolv_let':0
        }
    sql = "UPDATE zaci SET "+', '.join([pol+'=?' for pol in matrika.keys()])+" WHERE intern_kod='{}'".format(kod)
    print("SQL ({}): {} -- {}".format(args.wr, sql, tuple(matrika.values())))
    if args.wr:
        cur_wr.execute(sql, tuple(matrika.values()))

def baka_search(trida=None):
    """ search student in baka DB """
    #if rok != None:
    #    sql = "SELECT prijmeni, jmeno, trida, intern_kod FROM zaci WHERE YEAR(evid_od)={} ORDER by prijmeni,jmeno".format(rok)
    if trida != None:
        sql = "SELECT prijmeni, jmeno, trida, intern_kod FROM zaci WHERE trida='{}' ORDER by prijmeni,jmeno".format(trida)
    else:
        print(" -- nelze hledat v DB Bakaláři")
    cur.execute(sql)
    return cur

def pzk_search(prijmeni, jmeno):
    """ search in PZK db """
    #rint(prijmeni, jmeno)
    with pzk.cursor() as pzk_cur:
       sql = "select * from uchazec0 where prijmeni=%s and jmeno=%s"
       pzk_cur.execute(sql, (prijmeni.strip(), jmeno.strip()))
    return pzk_cur.fetchone()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zápis položek do DB Bakaláři z PZK")
    parser.add_argument("-r","--rok", help="evidence studenta od roku - povinný parametr")
    parser.add_argument("-t","--trida", help="zadej třídu - povinný parametr")
    parser.add_argument("-p","--pzk", action='store_true', help="přenést data z PZK do baka")
    parser.add_argument("-m","--matrika", action='store_true', help="nastavit výchozí data v matrice")
    parser.add_argument("-w","--wr", action='store_true', help="provede se zápis do db baka")
    args = parser.parse_args()

    # connect -- SQL Bakalari --
    #baka = ms.connect("bakalari-w2012","sa","Admin789","bakalari")
    baka = ms.connect("Driver={ODBC Driver 17 for SQL Server};Server=bakalari-w2012;UID=sa;PWD=Admin789;Database=bakalari;")

    cur = baka.cursor()
    cur_wr = baka.cursor()

    # connect -- PZK db --
    pzk = mysql.connect(host='proxy.gybon',user='selepzk',password='_sele_pzk_123',db='pzk',charset='utf8mb4',cursorclass=mysql.cursors.DictCursor)

    # --- utf8 - ascii ---
    intab = "áčďéěíľňóřšťúůýžöü"
    outab = "acdeeilnorstuuyzou"
    asci = str.maketrans(intab, outab)

    if args.trida and args.rok:
        print("Parametr: rok nástupu='{}', třída='{}'".format(args.rok, args.trida))
        res = baka_search(trida=args.trida).fetchall()
        for prijmeni, jmeno, trida, i_kod in res:
            print("{} {:<25} {}".format(trida.strip(), " ".join([prijmeni.strip(), jmeno.strip()]), i_kod))
            if args.pzk:
                baka_modify_pzk(i_kod, pzk_search(prijmeni, jmeno))
            if args.matrika:
                baka_modify_matrika(i_kod, args.rok)
    else:
        print("Není zadána třída nebo rok nástupu!")

    baka.commit()
