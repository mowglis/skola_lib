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

sub write_zam {
    #my ($db_baka) = @_;
    open_sql_bakalari();
    $cp = "utf8";
    print "$db_baka\n$dbf_ucitele\n";
    my $to_latin2  = new Cz::Cstocs "$cp",'il2';
    my $to_win1250 = new Cz::Cstocs "$cp",'1250';
    my $read_dbf = $db_baka->prepare("select * from $dbf_ucitele  where DELETED_RC!=1 order by prijmeni") or die $db_baka->errstr();
    $stredisko = "Zamìstnanci";
    $filename = "$akce\_pwk_zam.csv";
    print "$filename ($stredisko)...";
	$read_dbf->execute() or die $read_dbf->errstr();
	open(TRIDA,">$filename");
	while ($data = $read_dbf->fetchrow_hashref()) {
			$jmeno =    &$to_win1250(trim($data->{"JMENO"}));
			$prijmeni = &$to_win1250(trim($data->{"PRIJMENI"}));
			$rc = $data->{"RODNE_C"};
			$rc =~ s/\///g;
			$cip = $data->{"ISIC_CIP"};
			$cip2 = substr($cip,6,2). substr($cip,4,2). substr($cip,2,2). substr($cip,0,2);
			print TRIDA "$prijmeni;$jmeno;$rc;$cip2;$stredisko\n";
			print ".";
	}
	print "done\n";
	close(TRIDA);
    exit;
}

getopts("hdy:f:a");
$domain = "";
#$dbffile = $opt_f;
#$dbf_tridy = "TRIDY.DBF";
#$path = $opt_p;
#$cp = $opt_c;
$akce = "add";
$base_path_abs = '/opt/win/apps/bakalari-W2012/evid/absolv/';

if($opt_h) {
	# write help
   print "Vytvoreni csv importu studentu pro PowerKey\n";
   print "use: mkcsv-pwk_sql.pl [-y YYYY]\n
	volby:
	-d vytvoø soubor pro mazání u¾ivatelù z databáze - del
    -y rok
    -a data ze zaloh absolventu
    -f nazev dbf s absolventy
	-h tento help\n";
	exit;
}
my @date=localtime(time);
if ($opt_d) { $akce = "del"; }
if (!$opt_y)   {
    $rok = $date[5]+=1900;
} else {
    $rok = $opt_y;
}	 
if ($opt_a) {
    $path_abs = $base_path_abs."abs".$rok."/".$opt_z;
    open_db_bakalari($path_abs,$opt_f);
    printData;
    $cp = '1250';
} else {
    open_sql_bakalari();
    $cp = "utf8";
}
    my $to_latin2  = new Cz::Cstocs "$cp",'il2';
    my $to_win1250 = new Cz::Cstocs "$cp",'1250';
    my $read_dbf = $db_baka->prepare("select * from $dbf_zaci  where DELETED_RC!=1 AND trida=? order by prijmeni") or die $db_baka->errstr();
    my $read_tridy = $db_baka->prepare("select * from $dbf_tridy order by zkratka") or die $db_baka->errstr();
	print "Rok: $rok\n";
	@tridy = ();
	# naceni trid pro vyhledani - konec Ctrl-D  #
	while ($trida=<>) {
		chomp($trida);
        if ($trida eq 'Z') {
            write_zam($db_baka)
        }   
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
		$rocnik = substr($trida,1,1);
		$typ = 6; 
        $para = substr($trida,1,1);
		$stredisko = $rok-$rocnik;
		$stredisko .= '_'.$para.$typ;
		$filename = "$akce\_pwk_$trida.csv";
		print "$filename ($stredisko)...";
		open(TRIDA,">$filename");
		while ($data = $read_dbf->fetchrow_hashref()) {
#			$jmeno =    &$to_latin2($data->{"JMENO"});
			$jmeno =    &$to_win1250(trim($data->{"JMENO"}));
#			$prijmeni = &$to_latin2($data->{"PRIJMENI"});
			$prijmeni = &$to_win1250(trim($data->{"PRIJMENI"}));
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
