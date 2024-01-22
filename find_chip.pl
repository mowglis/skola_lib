#!/usr/bin/perl
# vyhleda cislo cipu vdb Bakalari
#
# veta:
#
#	options:
#	-f xbase (dbf) file
#	-p cesta k souboru dbf
#	-c kodovani vstupniho dbf
#	-x hexa cislo cipu

use lib '/home/rusek/lib';
use DBI;
use Cz::Cstocs;
use Getopt::Std;
use gybon;

getopts("f:p:c:hx:");

if($opt_h) {
	# write help
   print "vyhledava zadane cislo cipu v db\n";
   print "use: find_chip.pl -x hexa_id_chip  [-p path] [-f dbf_file] [-c codepage]\n
	volby:
	-x cislo ISIC cipu - 4B - 8 hexa cislic
	-p cesta do adresáøe s dbf soubory
	-f dbf soubor bez koncovky
	-c kódová stránka dat v dbf souboru (impl. cp1250)
	-h tento help\n";
	exit;
}
if($cp eq undef) {$cp = "1250";}
my $to_latin2 = new Cz::Cstocs "$cp",'il2';
my $to_win1250 = new Cz::Cstocs "$cp",'1250';
my $to_asci = new Cz::Cstocs "il2",'ascii';
my @date=localtime(time);
my $cip = $opt_x;
	$cip_rev = substr($cip,6,2). substr($cip,4,2). substr($cip,2,2). substr($cip,0,2);
	open_db_bakalari($opt_p,$opt_f,$opt_c);
my $read_dbf = $db_baka->prepare("select * from $dbf_zaci  where DELETED_RC!=1 AND (isic_cip=? OR isic_cip=?)") or die $db_baka->errstr();
#my $read_dbf = $db_baka->prepare("select * from $dbf_zaci  WHERE (isic_cip=? OR isic_cip=?)") or die $db_baka->errstr();

	printData;
	print "Finding: $cip or $cip_rev\n";
	$read_dbf->execute($cip,$cip_rev) or die $read_dbf->errstr();
	$nalezeno = 0;
	while ($data = $read_dbf->fetchrow_hashref()) {
			$nalezeno = 1;
#			print &$asci($data->{"TRIDA"})." ".&$asci($data->{"PRIJMENI"})." ".&$asci($data->{"JMENO"})." ".$data->{"POHLAVI"}."\n";
			$jmeno =    &$to_latin2($data->{"JMENO"});
			$prijmeni = &$to_latin2($data->{"PRIJMENI"});
#			$login = lcfirst(substr(&$to_asci($jmeno),0,3)).lcfirst(substr(&$to_asci($prijmeni),0,4));
			$rc = $data->{"RODNE_C"};
			$rc =~ s/\///g;
			$cip_db = $data->{"ISIC_CIP"};
			print "$prijmeni $jmeno - (RC: $rc): $cip_db (zadano: $cip)\n";
	}  
	if (!$nalezeno) {print "Nenalezeno!\n";}
	print "Done.\n";
