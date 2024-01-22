#!/usr/bin/env python3
"""
Module for Bakalari DB (MSSQL)
"""
#import pyodbc  as mssql
import pymssql as mssql
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

IBAN = {"kb":"CZ6101000000787768090287", "csas":"CZ5608000000001084862349"}

# --- utf8 => ascii ---
IN_CHAR  = "áčďéěíľňóřšťúůýžöüÁČĎÉĚÍĽŇÓŘŠŤÚŮÝŽÖÜ"
OUT_CHAR = "acdeeilnorstuuyzouACDEEILNORSTUUYZOU"
cz2ascii = str.maketrans(IN_CHAR, OUT_CHAR)
asci = lambda txt: txt.translate(cz2ascii)

rc = lambda x: x.replace('/', '')
to_cz_date = lambda dd: ".".join([dd[6:8], dd[4:6], dd[0:4]]) 
today = lambda : str(datetime.date.today()).replace('-','')
before_today = lambda days: str(datetime.date.today()-datetime.timedelta(days=days)).replace('-','')

def from_cz_date(date):
    """ from DD.MM.RRRR -> RRRRMMDD """
    two_digits = lambda x: x if len(x)==2 or len(x)==4   else '0'+x
    return ''.join([two_digits(dd) for dd in reversed(date.split('.'))])

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
    HOST = "proxy.gybon.cz"
    PORT = 587
    LOGIN = 'ru'
    PASSW = 'Maugl1s852456'
    TLS = True

    def __init__(self, mail_from='it@gybon.cz' , mail_to='rusek@gybon.cz' , mail_subj=''):
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
            msg.attach(MIMEImage(image))

        for f in mail_file: # attach files
            part = MIMEBase('application', "octet-stream")
            part.set_payload(open(f,"rb").read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="{0}"'.format(os.path.basename(f)))
            msg.attach(part)

        if send: # really send
            smtp = smtplib.SMTP(Mail.HOST, Mail.PORT)
            if Mail.TLS: smtp.starttls()
            smtp.login(Mail.LOGIN, Mail.PASSW)
            smtp.sendmail(send_from, send_to, msg.as_string())
            smtp.quit()
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
        ## with ODBC driver ##
        #driver = "{DRIVER=ODBC Driver 18 for SQL Server};server='%s';UID='%s';PWD='%s';Database='%s';" %  (Bakalari.HOST, Bakalari.USER, Bakalari.PASSW, Bakalari.DB)
        #self.conn = mssql.connect(driver, autocommit=True)
        ## --- pymssql --- ## 
        self.conn = mssql.connect(Bakalari.HOST, Bakalari.USER, Bakalari.PASSW, Bakalari.DB, autocommit=True, as_dict=True)
        self.cursor = self.conn.cursor()

    def __del__(self):
        self.conn.close()
 
    def select(self, sql, data=None):
        """ select DB """
        if data == None:
            self.cursor.execute(sql)               
        else:            
            self.cursor.execute(sql, data)               
  
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

    def student(self, prijmeni='', jmeno='', ikod='', login='', rc=''):
        """ create student from Baka """
        select_data = []
        #sql = "SELECT * FROM zaci, zaci_zzd, zaci_zzr WHERE zaci.intern_kod=zaci_zzr.intern_kod AND zaci_zzr.id_zz=zaci_zzd.id"
        sql = "SELECT zaci.* FROM zaci LEFT JOIN zaci_zzr ON zaci.intern_kod=zaci_zzr.intern_kod LEFT JOIN zaci_zzd ON zaci_zzr.id_zz=zaci_zzd.id WHERE zaci.deleted_rc=0"
        if prijmeni:
                sql += " AND zaci.prijmeni = %s"
                select_data += [prijmeni]
        if jmeno:
                sql += " AND zaci.jmeno = %s"
                select_data += [jmeno]
        if ikod:
                sql += " AND zaci.intern_kod = %s"
                select_data += [ikod]
        if login:
                sql += " AND zaci.username = %s"
                select_data += [login]
        if rc:
                sql += " AND zaci.rodne_c = %s"
                if '/' not in rc:
                    rc = rc[:-4]+'/'+rc[-4:]      
                select_data += [rc]

        self.select(sql, tuple(select_data))
        retval = self.cursor.fetchall()
        print(sql)
        print(retval)
        if len(retval) == 0:
            return None
        else:
            return Student(retval)

    def trida(self, trida):
        sql = "SELECT intern_kod, prijmeni, jmeno FROM zaci WHERE deleted_rc='false' AND trida = %s"
        self.select(sql, (trida))
        for s in self.cursor.fetchall():
            student = self.student(ikod=s[0])
            #print(student)
            if student == None:
                continue
            yield student                
        return 
        #return [self.student(ikod=s.intern_kod) for s in tr ]

    @property
    def tridy(self):
        """ seznam tříd """
        sql = "SELECT zkratka FROM tridy"
        ret = self.select(sql)
        return [ t.zkratka.strip()  for t in ret ]

class ZZ:
    """ zákonný zástupce """
    def __init__(self, prijmeni, jmeno, titul='', pohlavi='', telefon='', mobil='', email='', datovka='', prioritni=''):
        try:
            self.prijmeni = prijmeni.strip()
            self.jmeno = jmeno.strip()
            self.titul = titul.strip()
            self.pohlavi = pohlavi.strip()
            self.telefon = telefon.strip()
            self.mobil = mobil.strip()
            self.email = email.strip()
            self.datovka = datovka.strip()
            self.prioritni = prioritni
        except:
            pass

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "ZZ({}, {}, {}, {}, {}, {}, {}, {}, {})".format(self.prijmeni, self.jmeno, self.titul, self.pohlavi, self.telefon, self.mobil, self.email, self.datovka, self.prioritni)
    
class Student:
    """ gybon student 
    item 0-94    (95) zaci
    item 95-130  (36) zaci_zzd
    item 131-144 (14) zaci_zzr
    """
    old_login = lambda self: asci(self.jmeno[0:3].lower())+asci(self.prijmeni[0:4].lower())
    
    def __init__(self, items):
        self.print_items(items)
        item            = items[0]
        self.items      = items[0]
        self.trida      = item['TRIDA'].strip()
        self.prijmeni   = item['PRIJMENI'].strip()
        self.jmeno      = item['JMENO'].strip()
        self.datnar     = item['DATUM_NAR']
        self.rc         = item['RODNE_C'].strip()
        self.telefon    = item['TELEFON'].strip()
        self.mobil      = item['TEL_MOBIL'].strip()
        self.email      = item['E_MAIL'].strip()
        self.c_tr_vyk   = item['C_TR_VYK']
        self.ev_cislo   = item['EV_CISLO'].strip()
        self.login_db   = item['USERNAME'].strip()
        self.i_kod      = item['INTERN_KOD'].strip()
        try:
            self.covid_ock = item['COVID_OCK'].strftime("%d.%m.%Y")
        except:
            self.covid_ock = ''
        try:
            self.covid_poz = item['COVID_POZ'].strftime("%d.%m.%Y")
        except:
            self.covid_poz = ''

        if self.login_db == '':
            self.login = self.old_login()
        else:            
            self.login = self.login_db 
        self.zz = []
        ident = 114
        __zz = []
        for r in items:
            #print(r)
            # prijmeni, jmeno, titul , pohlavi , telefon , mobil , email , datovka , prioritni
            __zz = [ r[1+ident], r[ident+2], r[ident+3], r[ident+6], r[ident+7], r[ident+8], r[ident+9], r[ident+33], r[ident+44] ]
            self.zz += [ZZ(r[1+ident], r[ident+2], r[ident+3], r[ident+6], r[ident+7], r[ident+8], r[ident+9], r[ident+33], r[ident+44])]
    
    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "Student({}, {}, {}, {}, {}, {}, {}, {}, {})".format(self.i_kod, self.prijmeni, self.jmeno, self.datnar, self.rc, self.ev_cislo, self.email, self.mobil, self.login_db)
    
    def item(self, idx):
        return self.items[idx]

    def print_items(self, attr=None):
        """ print all items """
        print("=== List all items ===")
        print(type(attr))            
        print(attr)
        if not attr:
            attr=self.items
        if type(attr) != list:
            attr = [attr]
        for i in attr:
            for k,v in i.items():
                print("{}: {}".format(k, v))
        print("=== List items done. ===")

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
    
    def mail(self, message, mail_from='it@gybon.cz', mail_to='gybon', mail_subj='', mail_file=[], mail_image='', send=False):
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
        Mail().send(message, mail_from=mail_from, mail_to=_mail_to[mail_to], mail_subj=mail_subj, mail_file=mail_file, mail_image=mail_image, send=send)

    def update(self, cols):
        """ update student record """
        b = Bakalari()
       # print(self.i_kod, cols)
        b.update('zaci', cols, "zaci.intern_kod='{}'".format(self.i_kod))
        del(b)

    @property
    def firstname_lastname(self):
        return " ".join([self.jmeno, self.prijmeni])

    @property     
    def lastname_firstname(self):
        return " ".join([self.prijmeni, self.jmeno])

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
            sql += "AND SpecificSymbol = %s"
            select_data += [ss]
        elif id_akce:
            sql += "AND PaymentRegulation.Id = %s"
            select_data += [id_akce]
        self.b.select(sql, tuple(select_data))
        retval = self.b.cursor.fetchall()
        for item in retval:
            yield Platba_akce(item)    

    def student(self, akce, scope="all"):
        """ seznam studentů pro danou akci """
        if scope not in ['all', 'dluh', 'zaplaceno']:
            return None
        select_data = [akce._id]
        sql = "SELECT PersonId FROM Payments.PaymentRegulationPerson, Payments.PersonAccount WHERE Payments.PaymentRegulationPerson.PersonAccountId = Payments.PersonAccount.Id AND PaymentRegulationId = %s"
        self.b.select(sql, tuple(select_data))
        ikod = [item['PersonId'] for item in self.b.cursor]
        for ik in ikod:
            
            student = self.b.student(ikod=ik)
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
            sql += "PersonId = %s"
            select_data = (student.i_kod)
        elif akce and not student:
            sql += "PaymentRegulationId = %s"
            select_data = (akce._id)
        elif akce and student:
            sql += "PersonId = %s AND PaymentRegulationId = %s"
            select_data = (student.i_kod, akce._id)
        else:    
            return None

        self.b.select(sql, select_data) 
        for row in self.b.cursor.fetchall():
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
        self._id = item['PaymentRegulationId']
        self.title = item['Title']
        self.description = item['Description']
        self.payment_type = item['PaymentTypeId']
        self.ss = item['SpecificSymbol']
        self.bank_account = item['BankAccount']
        self.amount = item['Amount']

    def __str__(self):
        return "Platba_akce({}, {}, {}, {}, {}, {}, {})".format(self._id, self.title, self.description, self.payment_type, self.ss, self.bank_account, self.amount)

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

    def execute(self, sql, data=None):
        """ execute sql commnad """
        if data == None:
            self.cursor.execute(sql)
        else:
            self.cursor.execute(sql, data)
        return self.cursor            

    def update(self, table, cols, where):
        """ update DB """
        _set = ",".join(["=".join([k, '%s']) for k, v in cols.items()])
        data = tuple([v for k, v in cols.items()])
        sql = "UPDATE {} SET {} WHERE {}".format(table, _set, where)
        try:
            self.execute(sql, data)
            self.conn.commit()
            return 1
        except:
            return 0

    def insert(self, table, items):
        """ insert to DB """
        sql = "INSERT INTO {} ({}) VALUES ({})".format(table, ", ".join(items.keys()), ", ".join(['%s' for i in range(len(items.keys()))]))
        try:
            self.execute(sql, tuple(items.values()))
            self.conn.commit()
            return 1
        except:
            return 0

class It_DB(Mysql):
    """ DB it_gybon_cz (mysql) """
    HOST = "web.gybon"
    USER = "it_admin"
    PASSW = "admin789"
    DB = "it_gybon_cz"
    
    def __init__(self):
        super().__init__(It_DB.HOST, It_DB.USER, It_DB.PASSW, It_DB.DB)

class Eprihlasky_DB(Mysql):
    """ DB eprihlasky (mysql) """
    HOST = "web.gybon"
    USER = "it_admin"
    PASSW = "admin789"
    DB = "eprihlasky"
    
    def __init__(self):
        super().__init__(Eprihlasky_DB.HOST, Eprihlasky_DB.USER, Eprihlasky_DB.PASSW, Eprihlasky_DB.DB)

class Pzk_DB(Mysql):
    """ DB pzk (mysql) """
    HOST = "proxy.gybon"
    USER = "selepzk"
    PASSW = "_sele_pzk_123"
    DB = "pzk"
    
    def __init__(self):
        super().__init__(Pzk_DB.HOST, Pzk_DB.USER, Pzk_DB.PASSW, Pzk_DB.DB)

if __name__ == "__main__":
    
    print("\n*** test Bakaláři DB: Výpis tříd **")
    B = Bakalari()
    rows = B.select("SELECT * FROM tridy ORDER BY ZKRATKA")
    for row in rows:
        print(row.ZKRATKA, row.NASTUP, row.NAZEV)

    student = B.student(prijmeni='Vukmirovičová')
    print(student.prijmeni, student.jmeno, student.ev_cislo, student.trida, student.email, student.mobil, student.zz_email)
    
    student.QR(500, 'Klub rodičů', iban=IBAN['kb'], asci=True)
    student.mail("Message", mail_to='test') 
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

