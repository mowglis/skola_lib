#!/usr/bin/env python3
"""
prepare foto for import to Moodle
"""
import argparse
import pyodbc as ms
from datetime import date
import shutil
import os

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 

baka_folder = '/opt/win/apps/bakalari/evid/foto'
dest_folder = '/home/rusek/skola/bakalari_foto'

def add_text_image(login, name):
    """ add name to jpg file """
    foto = '/'.join([dest_folder, login])+".jpg"
    foto_new  = '/'.join([dest_folder, login])+".png" 
    font = ImageFont.truetype("fonts/FreeSansBold.ttf", 30)
    
    t_width, t_height = font.getsize(name)
   
    canvas = Image.new('RGB', (t_width + 20, t_height + 20), 'orange') 
    name_text = ImageDraw.Draw(canvas)
    name_text.text((10, 10), name, 'blue', font=font)

    img = Image.open(foto)
    #draw = ImageDraw.Draw(img)
    #draw.text((img.width, img.height), name, 'black', font=font, align='center')
    
    width, height = img.size
    x = (width - t_width) // 2
    y = height//2 + 120
    #draw.text((x, y), name, 'black', font=font, align='center')

    #Image.composite(canvas, img, canvas).save(foto_new, "PNG")
    img.paste(canvas, (x, y))

    img.save(foto)
    #canvas.save(foto_new, "PNG")

def baka_search(trida):
    """ search student in baka DB """
    sql = "SELECT prijmeni, jmeno, c_tr_vyk, username FROM zaci WHERE trida='{}' ORDER BY c_tr_vyk".format(trida)
    cur.execute(sql)
    return cur

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare foto for import to Moodle")
    parser.add_argument("-y", "--year", help="year - rok nástupu")
    parser.add_argument("-p", "--para", help="paralelka = A, B, C")
    parser.add_argument("-x", "--thisyear", help="Aktuální rok")
    parser.add_argument("-c", "--copy", action='store_true', help="Aktuální rok")
    parser.add_argument("-g", "--google", action='store_true', help="Foto pro Google")
    args = parser.parse_args()

    # connect -- SQL Bakalari --
    baka = ms.connect("Driver={ODBC Driver 17 for SQL Server};Server=bakalari-w2012;UID=sa;PWD=Admin789;Database=bakalari;")
    cur = baka.cursor()

    # --- utf8 - ascii ---
    intab = "áčďéěíľňóřšťúůýžöü"
    outab = "acdeeilnorstuuyzou"
    asci = str.maketrans(intab, outab)

    this_year = date.today().year if args.thisyear == None else args.thisyear
    get_login = lambda j,p : ''.join([j[0:3]+p[0:4]]).lower().translate(asci)

    if args.year and args.para:
        trida_folder = args.year+args.para+'6'
        trida = str(int(this_year)-int(args.year))+'.'+args.para
        print("Aktuální rok: {}".format(this_year))
        print("Rok nástupu: {} - paralelka: {} - folder: {} - třída: {}".format(args.year, args.para, trida_folder, trida))
        res = baka_search(trida).fetchall()
        source_folder = '/'.join([baka_folder, trida_folder])
        dest_folder = '/'.join([dest_folder, trida_folder])
        print("Zdroj a cíl kopie: {} --> {}".format(source_folder, dest_folder))
        if args.copy:
            try:
                os.mkdir(dest_folder)
                if args.google:
                    csv_file = open('/'.join([dest_folder, trida_folder])+".csv", "w")
            except FileExistsError:
                pass
        for prijmeni, jmeno, c_vyk, username in res:
            login = username.strip() if username.strip() != '' else get_login(jmeno, prijmeni)
            foto_baka = str(c_vyk)+".jpg"
            foto_moodle = login+".jpg"
            print("{:<25} {} -> {}".format(" ".join([prijmeni.strip(), jmeno.strip()]), foto_baka, foto_moodle))
            if args.copy:
                try:
                    shutil.copy2('/'.join([source_folder, foto_baka]), '/'.join([dest_folder, foto_moodle]))
                    add_text_image(login, " ".join([jmeno.strip(), prijmeni.strip()])) 
                    if args.google:
                        csv_file.write("{},{}\n".format(login, foto_moodle))
                except FileNotFoundError:
                    pass
        if args.copy:
            if not args.google:
                cmd = "(cd {}; zip {} *.jpg); mv {}.zip .; rm -rf {}".format(dest_folder, trida_folder, dest_folder+'/'+trida_folder, dest_folder)
                print(cmd)
                #os.system(cmd)
    else:
        print("Není zadán rok paralelka!")

