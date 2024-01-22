#!/usr/bin/env python3

import unicodedata
import subprocess 
import argparse

vpn_users="vpn_vnet.conf"
chap_file = "chap-secrets"
users_base_dir="/home/rusek/users"
_grep = "grep -r {} ../../users/* | grep users_ -m1"
ip_start = "10.100.100"
ip_last = 149

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Crate config chap-secrets for PPTP VPN")
    parser.add_argument("-c","--conf", help="file with new VPN users")
    args = parser.parse_args()

    if args.conf:
        vpn_users = args.conf
    f_users = open(vpn_users)
    f_out = open(chap_file, "w")
    f_in = open(".".join([chap_file, "template"]))
    u = [u.strip().split(":") for u in f_users if u[0] != "#"]

    for line in f_in:
        f_out.write(line)
    f_in.close()    

    for rok, jmeno, login in u:
        a_jmeno = unicodedata.normalize('NFKD', jmeno).encode('ascii','ignore').decode("ascii")
        #u_line = subprocess.check_output(_grep.format(a_jmeno), shell=True).decode("utf-8")
        u_line = subprocess.check_output(_grep.format(login), shell=True).decode("utf-8")
        passw = u_line.split(":")[2]
        ip_last += 1
        ip = ".".join([ip_start,str(ip_last)])
        line1 = " ".join(["# ---", jmeno, "---"])
        line2 = " ".join([login, "pptpd", passw, ip])
        print("\n".join([line1, line2]))
        f_out.write("\n".join([line1, line2, ""]))
