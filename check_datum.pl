#!/usr/bin/perl
#
# plni libovolnou polozku v databazi Bakalaru (ZACI)
#
use lib '/home/rusek/lib';
use DBI;
use Cz::Cstocs;
use Getopt::Std;
use gybon;

getopts("f:p:c:h");
$domain = "";
$cp = $opt_c;
$help = $opt_h;
#$rok = '2007';

if($dbf_zaci eq undef || $help) {
	# write help
   print "Plni polozku v databazi studentu\n";
   print "use: set_item_zaci.pl [-p db_path] [-f dbf_file] [-c codepage] -i polo¾ka -v hodnota\n
	volby:
	-p cesta do adresáøe s dbf soubory (impl. $db_path)
	-f dbf soubor bez koncovky (impl. $dbf_zaci)
	-c kódová stránka dat v dbf souboru (impl. cp1250)
	-w se zápisem do DBF souboru
	-i název polo¾ky
	-v hodnota
	-h tento help\n";
	exit;
}
#open_db_bakalari();
       if ($opt_f ne undef) { $dbf_zaci = $opt_f; }
        if ($opt_p ne undef) { $db_path  = $opt_p; }
        if ($opt_c eq undef) {$cp = "1250";} else {$cp = $opt_c;}
        $asci = new Cz::Cstocs "$cp",'il2';
        $db_baka = DBI->connect("DBI:XBase:$db_path")  or die $DBI::errstr;


my $read_dbf = $db_baka->prepare("select * from $dbf_zaci where trida=? order by prijmeni") or die $db_baka->errstr();
#my $write_dbf = $db_baka->prepare("update $dbf_zaci set $item=? where trida=? and c_tr_vyk=?") or die $db_baka->errstr();
printData();
print "Zadej tøídu (ENTER, konec dat CTRL-D): ";
while ($trida=<>) {
	chomp($trida);
	$read_dbf->execute($trida) or die $read_dbf->errstr();
	print "Tøída: $trida\n";
	while ($data = $read_dbf->fetchrow_hashref()) {
#		print &$asci($data->{"TRIDA"})." ".&$asci($data->{"PRIJMENI"})." ".&$asci($data->{"JMENO"})." ".$data->{"POHLAVI"}."\n";
		$jmeno     = &$asci($data->{"JMENO"});
		$prijmeni  = &$asci($data->{"PRIJMENI"});
		$sex       = $data->{"POHLAVI"};
		$datum_n   = $data->{"DATUM_NAR"};
		$rc        = $data->{"RODNE_C"};
		$status = 'ERROR';
		($den,$mes,$rok) = split(/\./,$datum_n);
		($_rc,$nic) = split (/\//,$rc);
		$den *= 1; $mes*=1; 
		$_rok = substr($_rc,0,2);
		$_mes = substr($_rc,2,2);
		if ($sex eq 'Z') { $_mes-=50; }
		$_den = substr($_rc,4,2); $_rok+=1900;
		if ($den == $_den && $mes == $_mes && $rok == $_rok) { $status = 'ok';}
		printf ("%s::%s DATNAR:%s-%s-%s  RC:%s-%s-%s...%s\n", $prijmeni,$jmeno,$den,$mes,$rok,$_den,$_mes,$_rok,$status);
	}
	print "\n";
	print "Zadej tøídu (ENTER, konec dat CTRL-D): ";
}
