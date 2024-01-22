#!/usr/bin/env python3
"""
import student to IT db
"""

from gybon import It_DB, asci
import argparse
import random
import sys
import os

PEOPLE_COLS = ['login', 'password', 'name', 'start', 'class', 'ttl', 'ad_context'] 

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Make file for import users to Gybon LAN")
    parser.add_argument("-y", "--yes", action="store_true", help="make changes -- yes to all")
    args = parser.parse_args()

    it = It_DB()
    for line in sys.stdin:
        if line[:1] == "#":
            continue
        else:    
            values = line.strip().split(':')
            #values.pop(3) # !!! pouze pro roky < 2021
            ad = values[3] 
            values[3], para_ttl = ad.split("_")
            values += [para_ttl[:1], para_ttl[1:2]]
            values += [ad]
            print(values[2], end='')
            if args.yes:
                if it.insert('people', dict(zip(PEOPLE_COLS, values))):
                    print("...add record")
                else:
                    print("...ERROR add record")
            else:
                print()
            
