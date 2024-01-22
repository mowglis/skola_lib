#!/usr/bin/env python3
"""
testovani - prace s AD
modul: ldap3
"""

import ldap3
ad_server = ldap3.Server('hal.gybon')
conn = ldap3.Connection(ad_server, user='ru@local.gybon', password='mauglis', auto_bind=True)
conn.search('ou=Teachers, dc=local, dc=gybon', '(objectclass=person)', attributes=['sAMAccountName','name','pager'])
#print(conn.entries)
for entry in conn.entries:
#    print(entry)
    print("Uživatel: {} -- účet: {} ".format(entry.name, entry.sAMAccountName))
