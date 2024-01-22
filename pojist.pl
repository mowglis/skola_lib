#!/usr/bin/perl
# vypisuje seznamy studentu z databaze Bakalaru
#
#	options:
#	-t typ 	0 - mesicni zemny (default)
#	    	1 - hromadne zmeny	
#	-h help

use lib '/home/rusek/lib';
use DBI;
use Cz::Cstocs;
use Getopt::Std;
use Socket qw(:DEFAULT :crlf);
use gybon;

sub  wr_rec {
  ($sign,$rc,$prijmeni,$jmeno,$datzm)=@_;
  $rc =~ s/\///g;
  printf "%1s%-10s%-30s%-24s%s%s", $sign,$rc,$prijmeni,$jmeno,$datzm,$CRLF;
}

getopts("t:m:a:x:r:h");
my $base_path_abs = '/opt/win/apps/bakalari/evid/absolv/';  # bakalari-W2012

if($opt_h) {
	# write help
   print "Vytvoreni vypise studentu\n";
   print "use: pojist.pl [-t type] [-m month] [-p path] [-f dbf_file] [-c codepage]\n
	volby:
	-t typ 0 = mesicni zmeny (default), 1 = hromadne zmeny
	-m mìsíc - pro mìsíèní soubor (typ 0)
	-a soubor absolventu
	-x cesta k souboru absolventu (doplnek)
	-r rok
	-h tento help
	!! Vystupní soubor je kódován v cp1250 !!\n";
	exit;
}
my $cs_dbf = new Cz::Cstocs "1250",'1250';
my $cs_sql = new Cz::Cstocs "utf8",'1250';

#my $db_baka = DBI->connect("DBI:XBase:$path")  or die $DBI::errstr;
open_sql_bakalari();

@datum = localtime(time);
$rok=$datum[5]+=1900;
if ($opt_m eq undef) {$mesic = $datum[4];}
	else {$mesic = $opt_m;}
#if($mesic < 9) {$rok+=1;}
$r=$rok;
if($mesic < 8) {$r=$rok-1;}
if (!($opt_r eq undef)) { $rok = $opt_r; }
$in_date='0109'.$r;
$out_date='3108'.$r;
#print STDERR  "* soubor studentù: ".$path."/".$dbffile."\n";
printf STDERR "* rok:%s mìsíc:%s\n", $rok, $mesic;
if ($opt_t eq undef || $opt_t eq 0) {
  # == mesicni zmeny -- co v tomto mesici dovrsili 15
  print STDERR "* Vytváøím mìsíèní zmìnový soubor\n";
  my $read_dbf = $db_baka->prepare("select * from zaci where (substring(datum_nar,7,4)=?-15) and ltrim(rtrim(substring(datum_nar,4,2)))=? order by trida,prijmeni") or die $db_baka->errstr();
  $read_dbf->execute($rok,$mesic) or die $read_dbf->errstr();
  while ($data = $read_dbf->fetchrow_hashref()) {
	  $dat_zm = $data->{"DATUM_NAR"};
	  $dat_zm =~ tr/ /0/; $dat_zm =~ s/\.//g;
	  $dat_zm = substr($dat_zm,0,4).$rok;
	  wr_rec('+',$data->{"RODNE_C"},$cs_sql->conv($data->{"PRIJMENI"}),$cs_sql->conv($data->{"JMENO"}),$dat_zm);
  }
} else {
  # == hromadne zmeny - prihlasit 1. rocniky (15ti lete), odhlasit abs.
  print STDERR "* Vytváøím soubor pro hromadné zmìny\n";
  # -- absolventi ven - odhlasit - data z DBF
  print STDERR "- odhlá¹ky absolventù\n";
  $dbf_abs_path = $base_path_abs.$opt_x;
  $dbf_abs = $opt_a;
  print STDERR "- soubor absolventù: ".$dbf_abs_path."/".$dbf_abs."\n";
  if($opt_a eq undef || $opt_x eq undef) {
    print STDERR "!!! nebyl zadán soubor absolventù !!!\n";
    print STDERR "-x cesta\n-a nazev souboru absolventu\n";
    exit();
  }	 
  my $db_baka_abs = DBI->connect("DBI:XBase:$dbf_abs_path")  or die $DBI::errstr;
  print STDERR "- odhlá¹ky absolventù ($dbf_abs_path/$dbf_abs)\n";
  my $read_dbf_abs = $db_baka_abs->prepare("select * from $dbf_abs where substr(trida,1,1)=? order by trida,prijmeni") or die $db_baka_abs->errstr();
  $read_dbf_abs->execute(6) or die $read_dbf_abs->errstr();
  while ($data = $read_dbf_abs->fetchrow_hashref()) {
	wr_rec('-',$data->{"RODNE_C"},$cs_dbf->conv($data->{"PRIJMENI"}),$cs_dbf->conv($data->{"JMENO"}),$out_date);
  }
  # -- 15-ti leti z prvaku ctyrleteho - prihlasit - data ze SQL
  print STDERR "- pøihlá¹ky prvákù\n";
  my $read_dbf = $db_baka->prepare("select * from zaci where substring(trida,1,1)=? and substring(datum_nar,4,2)<9 and ltrim(rtrim(substring(datum_nar,7,4)))<=?-15 order by trida,prijmeni") or die $db_baka->errstr();
  $read_dbf->execute(1,$rok) or die $read_dbf->errstr();
  while ($data = $read_dbf->fetchrow_hashref()) {
	wr_rec('+',$data->{"RODNE_C"},$cs_sql->conv($data->{"PRIJMENI"}),$cs_sql->conv($data->{"JMENO"}),$in_date);
  }
}

