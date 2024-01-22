#!/usr/bin/env python3
"""
import pzk data do DBF pro Baka

struktura dbf pro baka:
Num    Name        Type    Len Decimal
1. TRIDA           C       4       0
2. PRIJMENI        C       20      0
3. JMENO           C       12      0
4. BYDLISTE        C       40      0
5. PSC             C       6       0
6. DATUM_NAR       C       10      0
7. POHLAVI         C       1       0
8. RC              c       11      0
"""
import dbf
from gybon import Pzk_DB
tblname = 'zaci_new.dbf'

def create_table():
    return dbf.Table(tblname, 'trida C(4); prijmeni C(20); jmeno  C(20); bydliste C(50); psc C(6); datum_nar C(10); pohlavi C(1); rodne_c C(11)', codepage='cp1250')
    
sql_pzk = "SELECT id_studium,prijmeni,jmeno,pohlavi,datnar,ulice,misto,psc,ulice_cp,rc FROM uchazec0, trida WHERE uchazec0.id=trida.id_uchazec and  prijat AND paralelka=%s ORDER BY prijmeni, jmeno"

if __name__ == "__main__":
    pzk = Pzk_DB()
    table = create_table()
    table.open(mode=dbf.READ_WRITE)

    for paralelka in ['A', 'B', 'C']:
        sum = 0
        print("\nParalelka: {}".format(paralelka))
        for r in pzk.execute(sql_pzk, (paralelka,)):
            sum += 1
            print("{} {} {}".format(r['prijmeni'], r['jmeno'], r['datnar'].strftime('%d.%m.%Y')))
            pohlavi = 'M' if r['pohlavi'] == 1 else 'Z'
            bydliste = r['ulice']+' '+r['ulice_cp']+', '+r['misto']
            table.append(('0.{}'.format(paralelka), r['prijmeni'], r['jmeno'], bydliste, r['psc'], r['datnar'].strftime('%d.%m.%Y'), pohlavi, r['rc']))
        print("Celkem: {}".format(sum))
    
    table.close()
    del pzk
    print("Vytvořeno DBF: {}".format(tblname))

