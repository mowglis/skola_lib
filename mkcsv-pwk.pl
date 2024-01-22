#!/usr/bin/perl
# vypisuje seznamy studentu z databaze Bakalaru
# vytvori import soubor pro PWK - PowerKey
#
# veta:
# prijmeni;jmeno;RC;mifare_cip
#
#
#	options:
#	-f xbase (dbf) file
#	-p cesta k souboru dbf
#	-c kodovani vstupniho dbf
#	-h help

use lib '/home/rusek/lib';
use DBI;
use Cz::Cstocs;
use Getopt::Std;
use gybon;

getopts("f:p:c:hdy:");
$domain = "";
#$dbffile = $opt_f;
#$dbf_tridy = "TRIDY.DBF";
#$path = $opt_p;
#$cp = $opt_c;
$akce = "add";

if($opt_h) {
	# write help
   print "Vytvoreni csv importu studentu pro PowerKey\n";
   print "use: mkcsv-pwk.pl -p path -f dbf_file [-c codepage]\n
	volby:
	-p cesta do adresáøe s dbf soubory
	-f dbf soubor bez koncovky
	-c kódová stránka dat v dbf souboru (impl. cp1250)
	-d vytvoø soubor pro mazání u¾ivatelù z databáze - del
	-h tento help\n";
	exit;
}
if ($opt_d) { $akce = "del"; }
if($cp eq undef) {$cp = "1250";}
my $to_latin2 = new Cz::Cstocs "$cp",'il2';
my $to_win1250 = new Cz::Cstocs "$cp",'1250';
my $to_asci = new Cz::Cstocs "il2",'ascii';
my @date=localtime(time);
  if (!$opt_y) 
  {
    $rok = $date[5]+=1900;
  } else {
    $rok = $opt_y;
  }	 
#my $db_baka = DBI->connect("DBI:XBase:$path")  or die $DBI::errstr;
	open_db_bakalari($opt_p,$opt_f,$opt_c);
my $read_dbf = $db_baka->prepare("select * from $dbf_zaci  where DELETED_RC!=1 AND trida=? order by prijmeni") or die $db_baka->errstr();
my $read_tridy = $db_baka->prepare("select * from $dbf_tridy order by zkratka") or die $db_baka->errstr();
	printData;
	print "Aktuální rok: $rok\n";
	@tridy = ();
	# naceni trid pro vyhledani - konec Ctrl-D  #
	while ($trida=<>) {
		chomp($trida);
		if ($trida ne '*') {push(@tridy,$trida);}
	}
	# zapsat vsechny tridy #
	if ($trida eq '*') {
		while ($data_trida = $read_tridy->fetchrow_hashref()) {
			$read_tridy->execute() or die $read_tridy->errstr();
			$trida = $data_trida->{"ZKRATKA"};
			push(@tridy,$trida);
		}
	}
	foreach $trida (@tridy) {
		$read_dbf->execute($trida) or die $read_dbf->errstr();
		$trida =~ s/\.//g;
		if (substr($trida,0,1) eq 'S') {
			$rocnik = substr($trida,1,1);
			$typ = 6; $para = substr($trida,2,1);
		} else {
			$rocnik = substr($trida,0,1);
			$typ = 4; $para = substr($trida,1,1);
		}
		$stredisko = $rok-$rocnik+1;
		$stredisko .= '_'.$para.$typ;
		$filename = "$akce\_pwk_$trida.csv";
		print "$filename ($stredisko)...";
		open(TRIDA,">$filename");
		while ($data = $read_dbf->fetchrow_hashref()) {
#			print &$asci($data->{"TRIDA"})." ".&$asci($data->{"PRIJMENI"})." ".&$asci($data->{"JMENO"})." ".$data->{"POHLAVI"}."\n";
#			$jmeno =    &$to_latin2($data->{"JMENO"});
			$jmeno =    &$to_win1250($data->{"JMENO"});
#			$prijmeni = &$to_latin2($data->{"PRIJMENI"});
			$prijmeni = &$to_win1250($data->{"PRIJMENI"});
#			$login = lcfirst(substr(&$to_asci($jmeno),0,3)).lcfirst(substr(&$to_asci($prijmeni),0,4));
			$rc = $data->{"RODNE_C"};
			$rc =~ s/\///g;
			$cip = $data->{"ISIC_CIP"};
			$cip2 = substr($cip,6,2). substr($cip,4,2). substr($cip,2,2). substr($cip,0,2);
			print TRIDA "$prijmeni;$jmeno;$rc;$cip2;$stredisko\n";
			print ".";
		}
		print "done\n";
		close(TRIDA);
	}
