#!/usr/bin/env python3
"""
Module for Bakalari DB (pyODBC)
"""
import pyodbc  as mssql
import pymysql as mysql
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import COMMASPACE, formatdate
from email import encoders
import datetime
import os
import time
from rich import print
from random import choice
from string import ascii_uppercase, digits, punctuation


IBAN = {"kb":"CZ6101000000787768090287", "csas":"CZ5608000000001084862349"}

# --- utf8 => ascii ---
IN_CHAR  = "áčďéěíľňóřšťúůýžöüÁČĎÉĚÍĽŇÓŘŠŤÚŮÝŽÖÜ"
OUT_CHAR = "acdeeilnorstuuyzouACDEEILNORSTUUYZOU"
cz2ascii = str.maketrans(IN_CHAR, OUT_CHAR)
asci = lambda txt: txt.translate(cz2ascii)

rc = lambda x: x.replace('/', '')

def random_id(length):
    """ generate random id """
    my_punctation = [i for i in punctation if i != "'"]
    chars = [choice(choice([digits, ascii_uppercase, my_punctuation])) for i in range(length)]
    return ''.join(chars)

def format_attrib(dict_attr): 
    """ formátuje otributy objektu pro metodu __repr__ """
    def is_str(s):
        if isinstance(s, str):
            return "'"+s+"'"
        return str(s)
    return ", ".join([k+'='+is_str(v) for k, v in dict_attr.items()])

def from_cz_date(date, delimiter=''):
    """ from DD.MM.RRRR -> RRRRMMDD """
    two_digits = lambda x: x if len(x)==2 or len(x)==4   else '0'+x
    return delimiter.join([two_digits(dd.strip()) for dd in reversed(date.split('.'))])

# --- RRRRMMDD -> DD.MM.RRRR ---
to_cz_date = lambda dd: ".".join([dd[6:8], dd[4:6], dd[0:4]]) 

today = lambda : str(datetime.date.today()).replace('-','')
before_today = lambda days: str(datetime.date.today()-datetime.timedelta(days=days)).replace('-','')

def create_QR(am, xvs, xks, msg, xself, iban, asci=False):
    import qrcode
    from io import BytesIO, StringIO
    """ create QR code for payment 
    params:
    ACC: IBAN, BIC
    AM: částka 
    RF: ident platby pro příjemce
    MSG: zpráva pro příjemce
    X-VS: var symbol
    X-KS: konst symbol
    X-SELF: zpráva pro plátce
    """
    #text = "SPD*1.0*ACC:{}*AM:{}*CC:CZK*X-VS:{}*X-KS:{}*MSG:{}*X-SELF:{}".format(iban, am, xvs, xks, msg, xself)
    text = "SPD*1.0*ACC:{}*AM:{}*CC:CZK*X-VS:{}*X-KS:{}*MSG:{}".format(iban, am, xvs, xks, msg)
    #buff = BytesIO()
    qr = qrcode.QRCode(
        version=1,
        box_size=5,
        border=1)
    
    qr.add_data(text)
    qr.make(fit=True)
    if asci:
        f = StringIO()
        qr.print_ascii(out=f)
        f.seek(0)
        print(f.read())
    else:
        return qr.make_image(fill_color="black", back_color="white")

class Mail:
    """
    HOST = "proxy.gybon.cz"
    PORT = 587
    LOGIN = 'ru'
    PASSW = 'Maugl1s852456'
    TLS = True
    """
    # Google mail server
    HOST = "smtp.gmail.com"
    PORT = 587
    LOGIN = 'noreply@gybon.cz'
    PASSW = 'RW6Kb%BCyUqE8mY&%45'
    TLS = True
    
    def __init__(self, mail_from='noreply@gybon.cz' , mail_to='rusek@gybon.cz' , mail_subj=''):
        self._from = mail_from
        self._to = mail_to
        self._subj = mail_subj

    def send(self, message, mail_from='', mail_to='', mail_subj='', mail_file=[], mail_image='', send=False):
        """ pošle mail pomocí mailsererveru """
        send_from = mail_from if mail_from else self._from
        send_to   = mail_to   if mail_to   else self._to
        send_subj = mail_subj if mail_subj else self._subj

        msg = MIMEMultipart()
        msg['From'] = send_from
        msg['To']   = send_to
        msg['Date'] = formatdate(localtime = True)
        msg['Subject'] = mail_subj
        msg.preamble = 'This is a multi-part message in MIME format.'
        msg.attach(MIMEText(message))
        
        if mail_image != "": # attach image
            msg.attach(MIMEImage(mail_image))

        for f in mail_file: # attach files
            part = MIMEBase('application', "octet-stream")
            part.set_payload(open(f,"rb").read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="{0}"'.format(os.path.basename(f)))
            msg.attach(part)

        if send: # really send mail
            #try:
            smtp = smtplib.SMTP(Mail.HOST, Mail.PORT)
            if Mail.TLS: smtp.starttls()
            smtp.login(Mail.LOGIN, Mail.PASSW)
            #print("mail: {:20} ==> {:30}".format(send_from, send_to))
            smtp.sendmail(send_from, send_to, msg.as_string())
            smtp.quit()
            #except:
            #    print("mail: {:20} ==> {:30}".format(send_from, send_to))
        else:
            print("mail: {:20} ==> {:30}".format(send_from, send_to))

class Bakalari:
    """ DB Bakalari (MS SQL) """
    HOST = "bakalari-w2012"
    USER = "sa"
    PASSW = "Admin789"
    DB = "bakalari"
    
    def __init__(self):
        """ connect DB """
        driver = "Driver=ODBC Driver 17 for SQL Server;server={};UID={};PWD={};Database={};".format(Bakalari.HOST, Bakalari.USER, Bakalari.PASSW, Bakalari.DB)
        self.conn = mssql.connect(driver, autocommit=True)
        self.cursor = self.conn.cursor()

    def __del__(self):
        self.conn.close()
 
    def select(self, sql, data=None):
        """ select DB """
        if data == None:
            return self.cursor.execute(sql)               
        else:            
            return self.cursor.execute(sql, data)               

    def insert(self, table, vals):
        """ insert into DB
            - vals = dict
        """
        fields = ", ".join(vals.keys())
        data = tuple(vals.values())
        _data = ", ".join(['?' for i in range(len(data))])
        sql = 'INSERT INTO {} ({}) VALUES ({})'.format(table, fields, _data)
        print(sql, data)
        return self.cursor.execute(sql, data).rowcount

    def update(self, table, cols, where):
        """ update DB """
        _set = ",".join(["=".join([k, '?']) for k, v in cols.items()])
        data = tuple([v for k, v in cols.items()])
        sql = "UPDATE {} SET {} WHERE {}".format(table, _set, where)
        return self.cursor.execute(sql, data).rowcount

    def ucitel(self, prijmeni='', jmeno='', ikod='', login=''):
        """ create ucitel from Baka """
        select_data = []
        sql = "SELECT * FROM ucitele WHERE"
        if prijmeni:
                sql += " ucitele.prijmeni = ? AND"
                select_data += [prijmeni]
        if jmeno:
                sql += " ucitele.jmeno = ? AND"
                select_data += [jmeno]
        if ikod:
                sql += " ucitele.intern_kod = ? AND"
                select_data += [ikod]
        if login:
                sql += " ucitele.login = ? AND"
                select_data += [login]
        sql = sql[:-4]                
        #print(sql, select_data)
        try:
            retval = self.select(sql, tuple(select_data)).fetchone()
            if len(retval) == 0:
                return None
        except:
            return 
        return Ucitel(retval)

    def student_name(self, full_name):
        """ find and create student with full_name """
        name = full_name.split(' ')
        try:
            return self.student(prijmeni=name[0], jmeno=name[1])
        except:
            return self.student(prijmeni=name[0])

    def student(self, prijmeni='', jmeno='', ikod='', \
                login='', rc='', evcislo=''):
        """ select student from Baka """
        select_data = []
        sql = "SELECT * FROM zaci LEFT JOIN zaci_zzr ON \
                zaci.intern_kod=zaci_zzr.intern_kod \
                LEFT JOIN zaci_zzd ON zaci_zzr.id_zz=zaci_zzd.id \
                WHERE zaci.deleted_rc=0"
        if prijmeni:
                #sql += " AND zaci.prijmeni = ?"
                sql += " AND zaci.prijmeni \
                    COLLATE Czech_CI_AI  = ?"
                select_data += [prijmeni]
        if jmeno:
                #sql += " AND zaci.jmeno = ?"
                sql += " AND zaci.jmeno \
                    COLLATE Czech_CI_AI = ?"
                select_data += [jmeno]
        if ikod:
                sql += " AND zaci.intern_kod = ?"
                select_data += [ikod]
        if login:
                sql += " AND zaci.username = ?"
                select_data += [login]
        if rc:
                sql += " AND zaci.rodne_c = ?"
                if '/' not in rc:
                    rc = rc[:-4]+'/'+rc[-4:]      
                select_data += [rc]
        if evcislo:
                sql += " AND ev_cislo = ?"
                select_data += [evcislo]

        #print(sql, select_data)
        retval = self.select(sql, tuple(select_data)).fetchall()
        if len(retval) == 0:
            return None
        else:
            return Student(retval)

    def trida(self, trida):
        sql = "SELECT intern_kod FROM zaci WHERE deleted_rc='false' AND trida = ?" 
        for s in self.select(sql, (trida)).fetchall():
            student = self.student(ikod=s.intern_kod)
            if student == None:
                continue
            yield student                
        return 
        #return [self.student(ikod=s.intern_kod) for s in tr ]

    def get_ZZ(self, prijmeni=None, jmeno=None, ikod=None):
        """ get ZZ by, name, ikod """
        if prijmeni is None and jmeno is None and ikod is None:
            return
        sql = "SELECT * FROM zaci LEFT JOIN zaci_zzr \
            ON zaci.intern_kod=zaci_zzr.intern_kod \
                LEFT JOIN zaci_zzd ON zaci_zzr.id_zz=zaci_zzd.id \
                    WHERE zaci.deleted_rc=0"
        data = []
        if prijmeni is not None:
            sql += " AND zaci_zzd.prijmeni = ?"
            data += [prijmeni]
        if jmeno is not None:
            sql += " AND zaci_zzd.jmeno = ?"
            data += [jmeno]
        if ikod is not None:
            sql += " AND zaci_zzr.intern_kod = ?"
            data += [ikod]

        retval = self.select(sql, tuple(data)).fetchall()
        if len(retval) == 0:
            return None
        else:
            return [Student([r]) for r in retval]

    def add_ZZ(self, zz):
        """ add ZZ from PZK to DB 
            - zz - data from PZK
        """
        if not zz.ikod_student:
            return
        
        try:
            datum_nar = zz.datum_nar.strftime('%d.%m.%Y')
        except:
            datum_nar = ''            

        fields_zzd = {
            'ID':random_id(10),
            'PRIJMENI':zz.prijmeni,
            'JMENO':zz.jmeno,
            'TITUL':zz.titul,
            'DATUM_NAR':datum_nar,
            'POHLAVI':zz.pohlavi,
            'E_MAIL':zz.email,
            'TB_OBEC':zz.tb_obec,
            'TB_ULICE':zz.tb_ulice,
            'TB_CP':zz.tb_cp,
            'TB_PSC':zz.tb_psc[0:3]+' '+zz.tb_psc[3:],
            'DAT_SCHRAN':zz.datovka,
            'EVID_OD':datetime.datetime.now(),
            'MODIFIED':datetime.datetime.now()
        }
        fields_zzr = {
            'ID':random_id(10),
            'INTERN_KOD':zz.ikod_student,
            'ID_ZZ':fields_zzd['ID'],
            'VZTAH':'R',
            'JE_ZZ':1,
            'INFORMACE':1,
            'PRIMARNI':1,
            'PRIORITA':1
        }

        self.insert('zaci_zzd', fields_zzd)
        self.insert('zaci_zzr', fields_zzr)

    @property
    def tridy(self):
        """ seznam tříd """
        sql = "SELECT zkratka FROM tridy"
        ret = self.select(sql)
        return [ t.zkratka.strip()  for t in ret ]

class ZZ:
    """ ZZ - zákonný zástupce studenta """

    @classmethod
    def from_PZK(cls, pzk_uchazec, ikod_student=None):
        """ create ZZ from PZK uchazec record """
        pohlavi = lambda x: 'M' if x == 1 else 'Z'
        return ZZ(prijmeni=pzk_uchazec.zast_prijmeni, jmeno=pzk_uchazec.zast_jmeno, pohlavi=pohlavi(pzk_uchazec.zast_pohlavi), datovka=pzk_uchazec.datovka, email=pzk_uchazec.e_mail1, prioritni=True, informovat=True, datum_nar=pzk_uchazec.zast_datnar, ikod_student=ikod_student, tb_obec=pzk_uchazec.misto, tb_ulice=pzk_uchazec.ulice, tb_cp=pzk_uchazec.ulice_cp, tb_psc=pzk_uchazec.psc)   

    def __init__(self, prijmeni, jmeno, titul='', pohlavi='', telefon='', mobil='', email='', datovka='', prioritni=False, informovat=False, datum_nar='', ikod_student=None, tb_obec='', tb_ulice='', tb_cp='', tb_psc=''):
        try:
            self.prijmeni = prijmeni.strip()
            self.jmeno = jmeno.strip()
            self.titul = titul.strip()
            self.pohlavi = pohlavi
            self.telefon = telefon.strip()
            self.mobil = mobil.strip()
            self.email = email.strip()
            self.datovka = datovka.strip()
            self.prioritni = prioritni
            self.informovat = informovat
            # from PZK
            self.ikod_student = ikod_student
            self.datum_nar = datum_nar
            self.tb_obec = tb_obec
            self.tb_ulice = tb_ulice
            self.tb_cp = tb_cp
            self.tb_psc = tb_psc
        except:
            pass

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return 'ZZ('+format_attrib(self.__dict__)+')'
    
       
class Student:
    """ gybon student 
    item 0-99     (100) zaci
    
    item 102-115  (14)  zaci_zzr -- ZZ relation - vazba zaci-zzd
         108-121

    item 116-153  (36)  zaci_zzd -- ZZ data
         122-159 
    """
    old_login = lambda self: asci(self.jmeno[0:3].lower())+asci(self.prijmeni[0:4].lower())
    
    def __init__(self, items):
        item            = items[0]
        self.items      = items
        self.trida      = item[0].strip()
        self.prijmeni   = item[1].strip()
        self.jmeno      = item[2].strip()
        self.datnar     = item[22]
        self.rc         = item[23].strip()
        self.telefon    = item[25].strip()
        self.mobil      = item[26].strip()
        self.email      = item[27].strip()
        self.ev_cislo   = item[84].strip()
        self.login_db   = item[44].strip()
        self.i_kod      = item[91].strip()
        self.c_tr_vyk   = item[33]
        try:
            self.covid_ock = item[92].strftime("%d.%m.%Y")
        except:
            self.covid_ock = ''
        try:
            self.covid_poz = item[89].strftime("%d.%m.%Y")
        except:
            self.covid_poz = ''

        if self.login_db == '':
            self.login = self.old_login()
        else:            
            self.login = self.login_db 
        self.zz = []
        for r in items:
            __zz = self.get_zz_items(r)
            if len(__zz) > 0:
                self.zz += [ZZ(*__zz)]

    def get_zz_items(self, r):
        zz_record = {'prijmeni':123, 
                     'jmeno':124, 
                     'titul':125,
                     'pohlavi':128, 
                     'telefon':129, 
                     'mobil':130, 
                     'email':131, 
                     'datovka':155, 
                     'prioritni':116, 
                     'informovat':114}
        return [r[v] for k, v in zz_record.items() if r[v] != None]

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "Student({}, {}, {}, {}, {}, {}, {}, login={}, i_kod={})".format(self.prijmeni, self.jmeno, self.datnar, self.rc, self.ev_cislo, self.email, self.mobil, self.login_db, self.i_kod)

    def __eq__(self, other):
        try:
            return self.i_kod == other.i_kod
        except:
            return False

    def item(self, idx):
        return self.items[idx]

    def print_items(self, attr=None):
        """ print all items """
        print("=== print all items ===")
        if not attr:
            attr=self.items
        for items in attr:
            for i in range(len(items)):
                print("{}: {}".format(i, items[i]))
        print("=== Done ===")

    def absence(self, from_date=None, to_date=None, dic=False):
        """ absence studenta od-do """
        t_date = from_cz_date(to_date) if to_date else today()
        f_date = from_cz_date(from_date) if from_date else today()
        sql = "select * from absence where intern_kod=? and datum>=? and datum<=? order by datum, cislo_hod"
        b = Bakalari()
        try:
            l_abs =  [(to_cz_date(r[1]), int(r[4])-3) for r in b.select(sql, (self.i_kod, f_date, t_date))]
        except:
            l_abs = []
        if dic:
            d_abs = {}
            for date, hour in l_abs:
                try:
                    d_abs[date] += [hour]
                except KeyError:
                    d_abs[date] = [hour]
            return d_abs                    
        else:
            return l_abs
        
    @property
    def zz_email(self):
        """ mail na ZZ v prioritním pořadí """
        m =  [(zz.prioritni, zz.email) for zz in self.zz if zz.email != '']
        return [ mail for pri, mail in sorted(m, reverse=True) ]

    @property
    def fullname(self):
        return " ".join([self.prijmeni, self.jmeno])

    @property
    def zz_mobil(self):
        """ mobil na ZZ v prioritním pořadí """
        m =  [(zz.prioritni, zz.mobil) for zz in self.zz if zz.mobil != '']
        return [ mobil for pri, mobil in sorted(m, reverse=True) ]

    def QR(self, amount, text, iban, asci=False):
        """ create QR """
        msg = " ".join([self.jmeno, self.prijmeni, "-", self.trida])
        ks = "0008"
        vs = self.ev_cislo
        return create_QR(amount, vs, ks, msg, text, iban=iban, asci=asci)
    
    def mail(self, message, mail_from='noreply@gybon.cz', mail_to='gybon', mail_subj='', mail_file=[], mail_image='', send=False):
        """ mail to student 
            mail_to = ('gybon', 'private', 'zz', 'test')
        """
        try:
            _mail_to = {'gybon':"@".join([self.login, 'gybon.cz']), 
                'private':self.email, 
                'zz':self.zz_email[0], 
                'test':'rusek@gybon.cz'}
        except:                
            return
        #print("{} -> {}".format(mail_from, _mail_to[mail_to]))
        Mail().send(message, mail_from=mail_from, mail_to=_mail_to[mail_to], mail_subj=mail_subj, mail_file=mail_file, mail_image=mail_image, send=send)

    def update(self, cols):
        """ update student record """
        b = Bakalari()
       # print(self.i_kod, cols)
        b.update('zaci', cols, "zaci.intern_kod='{}'".format(self.i_kod))
        del(b)

class Ucitel:
    """ gybon Teacher """
    
    def __init__(self, item):
        self.items = item
        self.titul = item[0].strip()
        self.prijmeni = item[1].strip()
        self.jmeno = item[2].strip()
        self.datum_nar = item[23].strip()
        self.rc = item[24].strip()
        self.cislo_op = item[25].strip()
        self.pohlavi = item[26].strip()
        self.zkratka= item[27].strip()
        self.osob_cislo = item[29].strip()
        self.email = item[73].strip()
        self.tel_mobil = item[79].strip()
        self.login = item[88].strip()
        self.intern_kod = item[109].strip()
        try:
            self.covid_ock = item[104].strftime("%d.%m.%Y")
        except:
            self.covid_ock = ''
        try:
            self.covid_poz = item[103].strftime("%d.%m.%Y")
        except:
            self.covid_poz = ''

    def item(self, ind):
        """ get item with index """
        return self.items[ind].strip()

    def list_items(self):
        """ print all items """
        for i in range(len(self.items)):
            print("{}: {}".format(i, self.items[i]))
    
    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "Ucitel({}, {}, {}, {}, {}, {}, {}, {}, {})".format(self.prijmeni, self.jmeno, self.datum_nar, self.rc, self.osob_cislo, self.email, self.tel_mobil, self.login, self.intern_kod)

    def update(self, cols):
        """ update record """
        b = Bakalari()
        #print(self.intern_kod, cols)
        b.update('ucitele', cols, "ucitele.intern_kod='{}'".format(self.intern_kod))
        del(b)

    @property
    def fullname(self):
        return " ".join([self.prijmeni, self.jmeno])

class Platby:
    """ Platební modul BAKA """
    def __init__(self):
        self.b = Bakalari()

    def akce(self, title='', ss='', id_akce=''):
        """ platební akce """
        sql = "SELECT * FROM Payments.PaymentRegulation, Payments.PaymentRegulationLine WHERE PaymentRegulationLine.PaymentRegulationId = PaymentRegulation.Id "  
        select_data = []
        if title:
            sql += "AND PaymentRegulation.Title LIKE ?"
            select_data += ['%'+title+'%']
        elif ss:
            sql += "AND SpecificSymbol = ?"
            select_data += [ss]
        elif id_akce:
            sql += "AND PaymentRegulation.Id = ?"
            select_data += [id_akce]
        retval = self.b.select(sql, tuple(select_data)).fetchall()
        for item in retval:
            yield Platba_akce(item)    

    def student(self, akce, scope="all"):
        """ seznam studentů pro danou akci """
        if scope not in ['all', 'dluh', 'zaplaceno']:
            return None
        select_data = [akce.id]
        sql = "SELECT PersonId FROM Payments.PaymentRegulationPerson, Payments.PersonAccount WHERE Payments.PaymentRegulationPerson.PersonAccountId = Payments.PersonAccount.Id AND PaymentRegulationId = ?"
        ikod = [item[0] for item in self.b.select(sql, tuple(select_data))]
        for ik in ikod:
            student = self.b.student(ikod=ik)
            if student == None:
                continue
            if scope == 'dluh'   and self.student_platba(student, akce):
                continue
            if scope == 'zaplaceno' and not self.student_platba(student, akce):
                continue
            yield student
    
    def student_platba(self, student, akce):
        """ zda student akci již zaplatil """
        return len(list(self.platby(student=student, akce=akce))) > 0

    def akce_studenta(self, student):
        """ seznam akcí pro daného studenta """
        select_data = [student.i_kod]
        sql = "SELECT Payments.PaymentRegulation.*, Payments.PaymentRegulationLine.* FROM Payments.PaymentRegulation, Payments.PaymentRegulationLine, Payments.PaymentRegulationPerson, Payments.PersonAccount WHERE PaymentRegulation.Id = PaymentRegulationPerson.PaymentRegulationId AND  PaymentRegulationPerson.PersonAccountId = PersonAccount.Id AND PaymentRegulationLine.PaymentRegulationId = PaymentRegulation.Id AND PersonId = ?"
        for _akce in self.b.select(sql, tuple(select_data)).fetchall():   
            yield Platba_akce(_akce)

    def platby(self, student=None, akce=None):
        #ql = "SELECT * FROM Payments.PaymentRegulationLine, Payments.PaymentRegulationPerson, Payments.PersonAccount WHERE PaymentRegulationLine.PaymentRegulationPersonId = PaymentRegulationPerson.Id AND PaymentRegulationPerson.PersonAccountId = PersonAccount.Id AND "
        sql = "SELECT *  FROM Payments.DocumentLine, Payments.Document, Payments.PersonAccount, Payments.PaymentRegulation WHERE DocumentLine.DocumentId = Document.Id AND DocumentLine.PersonAccountId = PersonAccount.Id AND Document.PaymentRegulationId = PaymentRegulation.Id AND "
        if student and not akce:
            sql += "PersonId = ?"
            select_data = (student.i_kod)
        elif akce and not student:
            sql += "PaymentRegulationId = ?"
            select_data = (akce.id)
        elif akce and student:
            sql += "PersonId = ? AND PaymentRegulationId = ?"
            select_data = (student.i_kod, akce.id)
        else:    
            return None

        for row in self.b.select(sql, select_data).fetchall():
            yield Platba_line(row)

class Platba_line:
    def __init__(self, item):
        """ platba - Payments.PaymentRegulationLine """
        self.items = item
        #print(self.get_items())
        self.payment_regulation_id = item[25]
        self.inserted = item[1]
        self.modified = item[2]
        self.amount = item[6]
        self.bank_title = item[15]
        self.amount_def = item[17]
        self.vs = item[31]
        self.ikod = item[32]
        self.title = item[43]
        self.description = item[44]
        self.ss = item[46]

    def __str__(self):
        return "Platba_line({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})".format(self.payment_regulation_id, self.inserted, self.modified, self.amount, self.bank_title, self.amount_def, self.vs, self.ss, self.ikod, self.title, self.description)

    def __repr__(self):
        return self.__str__()

    def get_items(self):
        return [ (_id, item) for _id, item in enumerate(self.items)]

class Platba_akce:
    """" pravidelná platba - Payments.PaymentRegulation """
    def __init__(self, item):
        self.items = item
        #print(self.get_items())
        self.id = item[0]
        self.title = item[6]
        self.description = item[7]
        self.payment_type = item[8]
        self.ss = item[9]
        self.bank_account = item[10]
        self.active = item[16]
        self.amount = item[25]

    def __str__(self):
        return "Platba_akce(id={}, title='{}', description='{}', type={}, ss={}, account={}, amount={})".format(self.id, self.title, self.description, self.payment_type, self.ss, self.bank_account, self.amount)

    def __repr__(self):
        return self.__str__()

    def get_items(self):
        return [ (_id, item) for _id, item in enumerate(self.items)]

class Mysql:
    """ mysql """
    def __init__(self, host, user, passw, db):
        self.conn = mysql.connect(host=host, user=user, password=passw, db=db, charset='utf8mb4', cursorclass=mysql.cursors.DictCursor)
        self.cursor = self.conn.cursor()              

    def __del__(self):
        self.conn.close()

    def execute(self, sql, data=None, debug=None, new_cursor=False):
        """ execute sql commnad """
        if new_cursor:
            self.cursor = self.conn.cursor()
        if debug:
            print(sql, data)
            return
        try:
            if data == None:
                self.cursor.execute(sql)
            else:
                self.cursor.execute(sql, data)
        except mysql.Error as e:
            print("Error %d: %s" % (e.args[0], e.args[1]))
            return None
        return self.cursor            

    def select(self, sql, data=None, debug=None, new_cursor=False):
        return self.execute(sql, data=data, debug=debug, new_cursor=new_cursor)

    def update(self, table, cols, where, debug=None):
        """ update recs """
        _set = ",".join(["=".join([k, '%s']) for k, v in cols.items()])
        data = tuple([v for k, v in cols.items()])
        sql = "UPDATE {} SET {} WHERE {}".format(table, _set, where)
        self.execute(sql, data=data, debug=debug)
        self.conn.commit()
        return 1

    def insert(self, table, items, debug=None):
        """ insert into  table """
        sql = "INSERT INTO {} ({}) VALUES ({})".format(table, ", ".join(items.keys()), ", ".join(['%s' for i in range(len(items.keys()))]))
        self.execute(sql, data=tuple(items.values()), debug=debug)
        self.conn.commit()
        return 1

    def delete(self, table, where=None, debug=None):
        """ delete record from table """
        sql = "DELETE FROM {}".format(table)
        data = ()
        if where:
            sql += " WHERE {}".format(" AND ".join([k+'=%s' for k in where]))
            data = tuple(where.values())
        self.execute(sql, data, debug=debug)
        self.conn.commit()
        return 1

class Gybon_moodle(Mysql):
    HOST = "web.gybon"
    USER = "moodle_gybon_admin"
    PASSW = "m00dle123*"
    DB  = "gybon_moodle"

    def __init__(self):
        super().__init__(Gybon_moodle.HOST, Gybon_moodle.USER, \
                         Gybon_moodle.PASSW, Gybon_moodle.DB)

    def delete_all_tables(self):
        """ delete all tables of db """
        tables = ['choice', 'choice_options', 'choice_answers']
        [self.delete(table=table, debug=False) for table in tables]

    def insert_choice(self, choice, answers, debug=False):
        """ insert records to tables """
        options = choice.__dict__.pop('options')
        self.insert(table='choice', items=choice.__dict__, debug=debug)
        for option in options:
            items = option.__dict__
            items['choiceid'] = choice.id
            items['optionid'] = items['id']
            del items['id']
            self.insert(table='choice_options', items=items, debug=debug)
        for answer in answers:
            self.insert(table='choice_answers', items=answer, debug=debug)

class Moodle(Mysql):
    """  DB moodle (mysql) """
    HOST = "web.gybon"
    USER = "moodle_read"
    PASSW = "m00dle123"
    DB  = "moodle"

    def __init__(self):
        super().__init__(Moodle.HOST, Moodle.USER, \
                         Moodle.PASSW, Moodle.DB)

    def choice_options(self, id):
        """ id = id choice """
        sql = "select id, text, maxanswers from mdl_choice_options where choiceid=%s"
        c = self.select(sql, (id,), new_cursor=True)
        return [Moodle_choice_option(rec) for rec in c]

    def choice_answers(self, choice):
        """" answers of choice """
        sql = "SELECT username, firstname, lastname FROM mdl_choice_answers, mdl_user \
            WHERE userid=mdl_user.id AND choiceid=%s AND optionid=%s"
        b = Bakalari()
        answers = {}
        for  option in choice.options:
            answers[option.id] = []
            c = self.select(sql, (choice.id, option.id))
            for rec in c:
                student = b.student(login=rec['username'])
                if not student:
                    student = b.ucitel(login=rec['username'])
                if student:
                    answers[option.id] += [student]
        return answers                 

    def choice(self, name=None, id=None):
        """" ankety """ 
        sql = "select id, course, name, intro from mdl_choice"
        data = []
        if name != None:
            sql += " WHERE name LIKE %s"
            data += [name] 
        elif id != None:
            sql += " WHERE mdl_choice.id = %s"
            data += [id]
        cursor  = self.select(sql, tuple(data))
        for rec in cursor:
            yield Moodle_choice(rec, self.choice_options(rec['id']))

class Moodle_choice():

    def __init__(self, choice_row, options=[]):
        self.__dict__.update(choice_row)
        self.options = options

    def __str__(self):
        _str = ", ".join(["{}={}".format(attribute, value) for \
                          attribute, value in self.__dict__.items() if attribute != 'intro'])
        return "Moodle_choice("+_str+")"

class Moodle_choice_option():

    def __init__(self, option_row):
        self.__dict__.update(option_row)

    def __str__(self):
        _str = ", ".join(["{}={}".format(attribute, value) for attribute, value in self.__dict__.items()])
        return "Moodle_choice_option("+_str+")"

    def __repr__(self):
        return self.__str__()

class It_DB(Mysql):
    """ DB it_gybon_cz (mysql) """
    HOST = "web.gybon"
    USER = "it_admin"
    PASSW = "admin789"
    DB = "it_gybon_cz"
    
    def __init__(self):
        super().__init__(It_DB.HOST, It_DB.USER, It_DB.PASSW, It_DB.DB)

class Eprihlasky_application():
    """ Application """
    def __init__(self, db_row):
         if db_row is not None:
            for key, value in db_row.items():
                setattr(self, key, value)

    def __str__(self):
        _str = ", ".join(["{}={}".format(attribute, value) for attribute, value in self.__dict__.items()])
        return "Eprihlasky_application("+_str+")"

    def date_as_str(self, attr_name):
        try:
            return self.__dict__[attr_name].strftime('%d.%m.%Y')
        except:
            return ''
        
class Eprihlasky_DB(Mysql):
    """ DB eprihlasky (mysql) """
    HOST = "web.gybon"
    USER = "eprihlasky_remote"
    PASSW = "admin789"
    DB = "eprihlasky"
    
    def __init__(self):
        super().__init__(Eprihlasky_DB.HOST, Eprihlasky_DB.USER, Eprihlasky_DB.PASSW, Eprihlasky_DB.DB)

    def get_application(self, idPaymentBaka):
        """ podpisová akce z tabulky published_application podle idPaymentBaka """
        sql = "select * from published_applications where idPaymentsBaka=%s"
        try:
            self.application = Eprihlasky_application(self.execute(sql,(idPaymentBaka)).fetchone())
            return self.application
        except:
            return None        
        
    def students(self, application=None):
        """ studenti podpisové akce """
        sql = "select * from signees where publishedApplicationId=%s and signedOn IS NULL order by studentSurname"
        try:
            app = self.application if application is None else application
            result = self.execute(sql, (app.id)).fetchall()
            return result
        except:
            return None

    def check_signature(self, ikod, application=None):
        """" kontrola podpisu přihlášky studentem """
        sql = "select * from signees where publishedApplicationId=%s and studentINTERN_KOD=%s and signedOn IS NOT NULL"
        app = self.application if application is None else application
        result = self.execute(sql, (app.id, ikod)).fetchone()
        return result != None

    def get_ikod(self, application=None):
        """ seznam ikodů studentů podpisové akce """
        sql = "select * from signees where publishedApplicationId=%s"
        app = self.application if application is None else application
        try:
            result = self.execute(sql,(app.id,))
            return [row['studentINTERN_KOD'] for row in result.fetchall()]
        except:
            return None

    def delete_ikod(self, application=None, list_ikod=None):
        """ smaže věty v application podle seznamu ikódů """
        app = self.application if application is None else application
        where = {'publishedApplicationId':app.id}
 
        for ikod in list_ikod:
            where['studentINTERN_KOD'] = ikod
            self.delete('signees', where, debug=None)  

    def add_students(self, application=None, students=None):
        """ přidá věty do application podle seznamu ikódů """
        app = self.application if application is None else application
        items = {
            'publishedApplicationId':app.id,
            'signed':0,
            'created': datetime.datetime.today()
            }

        #print(students)        
        for s in students:
            items['studentINTERN_KOD'] = s.i_kod
            items['studentFirstname'] = s.jmeno
            items['studentSurname'] = s.prijmeni
            items['studentClass'] = s.trida
            items['studentBornOn'] = from_cz_date(s.datnar,'-')
            self.insert('signees', items=items, debug=False)

class Pzk_uchazec():

    def __init__(self, record):
        self.__dict__.update(record)

    def __repr__(self):
        return "Pzk_uchazec("+format_attrib(self.__dict__)+")"

class Pzk_DB(Mysql):
    """ DB pzk (mysql) """
    HOST = "proxy.gybon"
    USER = "selepzk"
    PASSW = "_sele_pzk_123"
    DB = "pzk"
    
    def __init__(self):
        super().__init__(Pzk_DB.HOST, Pzk_DB.USER, Pzk_DB.PASSW, Pzk_DB.DB)

    def uchazec(self, prijmeni, jmeno=None):
        """ vyhledej uchazeče podle příjmení a jména"""
        sql = "SELECT * FROM uchazec0 where prijmeni=%s"
        if jmeno:
            sql += " AND jmeno=%s"
            data = (prijmeni, jmeno) 
        else:
            data = (prijmeni,)
        cur = self.select(sql, data)
        return Pzk_uchazec(cur.fetchone())

if __name__ == "__main__":
    
    print("\n*** test Bakaláři DB: Výpis tříd **")
    B = Bakalari()
    rows = B.select("SELECT * FROM tridy ORDER BY ZKRATKA")
    for row in rows:
        print(row.ZKRATKA, row.NASTUP, row.NAZEV)

    # test - výpis studenta
    print("\n*** test Bakaláři DB: Výpis studenta **")
    prijmeni_student = 'Vukmirovičová'
    print("Výpis studenta: {}".format(prijmeni_student))
    student = B.student(prijmeni=prijmeni_student)
    print(student)
    #print(student.__dict__)
    print(student.prijmeni, student.jmeno, student.ev_cislo, student.trida, student.email, student.mobil, student.zz_email)

    student.QR(500, 'Klub rodičů', iban=IBAN['kb'], asci=True)
    student.mail("Message", mail_to='test', mail_subj="Testovací zpráva - gybon.py", send=True) 
    del B        

    print("\n*** test IT DB: list table 'os' ***")
    it = It_DB()
    rows = it.execute("SELECT * from os")
    for row in rows:
        print(row['os'])
    del it

    print("\n*** test PZK DB: list table 'prum' ***")
    pzk = Pzk_DB()
    rows = pzk.execute("SELECT * from prum")
    for row in rows:
        print(row['od'], row['do'], row['body'])
    del pzk

