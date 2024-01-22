#!/usr/bin/perl
#
# ISIC
#
use lib '/home/rusek/lib';
use DBI;
use Cz::Cstocs;
use Getopt::Std;
use gybon;
use Data::Dumper;
use POSIX 'strftime';

sub print_result {
    my ($code, $sw) = @_;
    @info = (
        "ok",
        "error - code chip mismatch",
        "error - record not found"
    );
    printf STDERR "** result - %5s: %s \n",$sw, $info[$code];
}

sub write_csv {
    #
    # write csv file and upload to server
    # 
    my ($csv) = @_;
    my $temp_dir = "/mnt/safeq/";
    my $filename = "student_card.csv";
    # -- read file 
    my @cards = ();
    open  $fh, '<', $temp_dir.$filename or die $!;
    while ( $line=<$fh> ) { $line =~ s/[\r\n]+//; push @cards, $line; }
    close $fh;
    foreach my $item ( @$csv ) {
        my ( $login, $card ) = split(/;/, $item);
        my ( $index ) = grep { $cards[$_] =~ /$login/ } 0..$#cards;
        if ( $index ) { 
            $cards[$index] = $item;
        } else {
            push @cards, $item;
        }            
    }
    # -- write file
    open  $fh, '>', $temp_dir.$filename or die $!;
    foreach $line ( @cards ) { print $fh $line."\r\n"; }
    close $fh;
    print STDERR "\nCSV file '$filename' updated.\n";
#    system("smbclient $upload -U ru%mauglis -c \"lcd $temp_dir; put  $filename\"");
#    system("rm -f $filename");
#    print "CSV file '$filename' uploaded to '$upload'.\n";
    return;
}

sub append_csv {
    #
    # prepare csv data 
    #
    my ( $safeq, $baka_data, $csv ) = @_;
    my $baka_cip = trim(reverse_hex(trim($baka_data->{'isic_cip'})));
    my $login = $safeq->{'login'}; 
 #   push @{ $csv }, "$login;\r\n";
    push @{ $csv }, "$login;$baka_cip\r\n";
    print STDERR "** SafeQ: card updated\n";
}

sub update_pwk_card {
    #
    # update card data in PwK db
    #
    my ($db_pwk, $pwk, $baka_data) = @_;
    my $name_surname = trim($pwk->{'firstname'}).' '.trim($pwk->{'surname'});
    my $baka_cip = reverse_hex(trim($baka_data->{'isic_cip'}));
    my $int_baka_cip = hex_to_int($baka_cip);
    my $person_id = trim($pwk->{'person_id'});
    $sql_update_card = sprintf
"SET NOCOUNT ON
BEGIN TRANSACTION
DECLARE \@TouchID int
DECLARE \@TouchOwnerID int
SET \@TouchID=NULL
SET \@TouchOwnerID=NULL
EXECUTE \@TouchID = pwk.PwkTable_GetNewID 11
EXECUTE \@TouchOwnerID = pwk.PwkTable_GetNewID 12
INSERT pwk.Touch(TouchID, MediumType, TouchCodeLo, TouchCodeHi) VALUES (\@TouchID, 2, ?, 0)
INSERT pwk.Touch_Owner(TouchOwnerID, TouchID, OwnerType, AttachDate, IsActive, AttachedByID, TouchName) VALUES (\@TouchOwnerID, \@TouchID, 1, GetDate(), 1, 4, '%s')
INSERT pwk.Person_TouchOwner(PersonID, TouchOwnerID) VALUES (%s, \@TouchOwnerID)
COMMIT", $name_surname, $person_id;

    $sql_update_touchcode = "UPDATE pwk.Touch SET TouchCodeLo=? WHERE TouchID=?";
    $sql_update_date = "UPDATE pwk.Touch_Owner SET AttachDate=GetDate() WHERE TouchID=?";
    $touch_id = $pwk->{'touch_id'};
#    print "update_pwk_card: $sql_update_card\n";
#    print "update_pwk_touchcode: $sql_update_touchcode\n";
#    print "name_surname: $name_surname\n";
#    print "baka_cip: $baka_cip\n";
#    print "int_baka_cip: $int_baka_cip\n";
#    print "person_id: $person_id\n";
#    print "touch_id: $touch_id\n";
#    $stm_1 = $db_pwk->prepare("SELECT TouchID FROM pwk.Touch WHERE MediumType=2 AND TouchCodeLo=? AND TouchCodeHi=0");
#    $stm = $db_pwk->prepare( $sql_update_card );
#    $stm->execute($int_baka_cip);
    $db_pwk->do($sql_update_touchcode, undef, $int_baka_cip, $touch_id);
    $db_pwk->do($sql_update_date, undef, $touch_id);
    print STDERR "** PwK: card updated\n";
}

sub print_data {
    ($data, $pwk_rec, $pwk_result, $safeq_rec, $safeq_result, $long_type) = @_;
    print_baka($data, $long_type);
    print_pwk($pwk_rec, $long_type);
#    print_safeq($safeq_rec, $long_type);
    print_result($pwk_result,'PwK');
#    print_result($safeq_result,'SafeQ');
}

sub print_safeq {
    my ($safeq, $long_type) = @_;
    if ($long_type) {
        printf "\n=== SafeQ ===\n";
        printf "Name:        %s %s\nLogin:       %s\nEmail:       %s\nOU:          %s\nHomedir:     %s\nCard:        [%s]\n", trim($safeq->{'surname'}), trim($safeq->{'user_name'}), trim($safeq->{'login'}), trim($safeq->{'email'}), trim($safeq->{'ou_name'}), trim($safeq->{'homedir'}), disp_code($safeq->{'card'});
    } else {
        printf STDERR " :: SafeQ [%s]", disp_code($safeq->{'card'});
    }
    if (!$safeq && !$long_type) { printf STDERR " %s ", '*no record*'; }
    print "\n";
}

sub print_baka {
    ($data, $long_type) = @_;
    $baka_cip = reverse_hex ($data->{'isic_cip'});
    if ($long_type) {
        printf ("\n=== IS Bakaláři ===\n");
        printf ("Student:    %s %s (%s)\nNarození:   %s (RČ: %s)\nISIC karta: %s\nISIC čip:   %s -> [%s]\nISIC valid: %s\nISIC datum: %s\nlogin:      %s\n", trim($data->{"prijmeni"}), trim($data->{"jmeno"}), trim($data->{'trida'}), trim($data->{"datum_nar"}), $data->{"rodne_c"}, trim($data->{"isic_karta"}), trim($data->{"isic_cip"}), disp_code($baka_cip), isic_valid(trim($data->{'isic_plat'})), $data->{'isic_objdt'}, $data->{'username'});
    } else {
        printf STDERR "\n%s %s (%s): Bakaláři [%s]", trim($data->{'prijmeni'}), trim($data->{'jmeno'}), trim($data->{'trida'}), disp_code($baka_cip); 
    }
}

sub print_pwk {
    my ($pwk, $long_type) = @_;
    my $pwk_cip = int_to_hex(trim($pwk->{'touchcodelo'}));
    if ($long_type) {
        printf ("\n=== PowerKey ===\n");
        printf "Person:      %s %s\nPersonalNum: %s\nTouchCodeLo: %s -> [%s]\nAttachDate:  %s\n", trim($pwk->{'surname'}), trim($pwk->{'firstname'}), trim($pwk->{'personalnum'}), trim($pwk->{'touchcodelo'}), disp_code($pwk_cip), trim($pwk->{'attachdate'});
    } else {
        printf STDERR " :: PwK [%s]", disp_code($pwk_cip);
    }
    if (!$pwk && !$long_type) { printf STDERR " %s ", '*no record*'; }
    print "\n";
}

sub get_safeq_data {
    my ($db_safeq, $baka, $long_type) = @_;
    my $asci = new Cz::Cstocs('utf8','ascii');
    my $baka_cip = reverse_hex(trim($baka->{'isic_cip'}));
    if ( trim($baka->{'username'}) eq '' ) {
        # set login name
        $login = lc substr(&$asci(trim($baka->{'jmeno'})), 0, 3).substr(&$asci(trim($baka->{'prijmeni'})), 0, 4); 
    } else {
        $login = trim($baka->{'username'});
    }
    # print "login: $login\n";
    my $stm = $db_safeq->prepare("SELECT login, surname, users.name as user_name, email, users_ou.name as ou_name, homedir, card FROM users, users_cards, users_ou  WHERE users.id=users_cards.user_id AND users.ou_id=users_ou.id AND login = ? ORDER BY surname, users.name");
    my $stm_2 = $db_safeq->prepare("SELECT login, surname, users.name as user_name, email, users_ou.name as ou_name, homedir  FROM users, users_ou  WHERE users.ou_id=users_ou.id AND login = ? ORDER BY surname, users.name");
   $stm->execute($login);
    if ($stm->rows > 0) {
        $errcode = 1;
    } else {
        $errcode = 2; # no record
        $stm_2->execute($login);
        $safeq = $stm_2->fetchrow_hashref();
        return ($safeq, $errcode);
    }
    #print "num_recs: ".$stm->rows."\n";
    my $safeq_rec = 0;    
    while ( $safeq = $stm->fetchrow_hashref() ) {
        $safeq_rec = $safeq;
        if ($safeq->{'card'} == $baka_cip ) {
            $errcode = 0;
            $safeq_rec = $safeq;
            return ($safeq_rec, $errcode);
            break;
        }
    }
    return ($safeq_rec, $errcode);
}

sub get_pwk_data {
    # *** read data from pwk DB ***
    my ($db_pwk, $baka_data) = @_;
    my $baka_cip = reverse_hex(trim($baka_data->{'isic_cip'}));
    my $personalNum = $baka_data->{'rodne_c'};
#    $sql = "select surname, firstname, personalnum, touchcodelo from pwk.person, pwk.person_touchowner, pwk.touch_owner, pwk.touch  where pwk.person.personid=pwk.person_touchowner.personid and pwk.person_touchowner.touchownerid=pwk.touch_owner.touchownerid and pwk.touch_owner.touchid=pwk.touch.touchid and isactive=1  and personalnum=?";
    $personalNum =~ s/\///g;
    $personalNum =~ s/^0*//g;
    $sql_templ ="SELECT TOP 1 pwk.person.personID as person_id, pwk.touch.touchid as touch_id, surname, firstname, personalnum, touchcodelo, attachdate FROM pwk.person, pwk.person_touchowner, pwk.touch_owner, pwk.touch WHERE pwk.person.personid=pwk.person_touchowner.personid AND pwk.person_touchowner.touchownerid=pwk.touch_owner.touchownerid AND pwk.touch_owner.touchid=pwk.touch.touchid AND MediumType=2";
    @sql_statements = (
        [ $sql_templ." AND personalnum=? ORDER BY AttachDate DESC",
            [ $personalNum ]
        ],
        [ $sql_templ." and surname=? and firstname=? order by attachdate desc",
            [ trim($baka_data->{'prijmeni'}), trim($baka_data->{'jmeno'}) ]
        ]);
    my $pwk_rec = 0;
    $errcode = 2;
    foreach my $sql (@sql_statements) {
        my $read_pwk = $db_pwk->prepare($sql->[0]) or die $db_pwk->errstr;
        $read_pwk->execute(@{ $sql->[1] });
        while ($pwk = $read_pwk->fetchrow_hashref()) {
            if (!$pwk_rec) {
                $errcode = 1;
                $pwk_rec = $pwk;
            }
            $pwk_cip = int_to_hex(trim($pwk->{'touchcodelo'}));
            if ($baka_cip eq $pwk_cip) {
                $errcode = 0;
                $pwk_rec = $pwk;
                break;
            }
        }
        if (!$errcode) { last; } 
    }    
    return ($pwk_rec, $errcode);
}

sub isic_valid {
    ($_isic) = @_;
    @items = split /\//, $_isic;
    $last_y = $items[1]+1;
    return $_isic."-12/".$last_y;
}

sub disp_code {
    my ( $code ) = @_;
    $code = trim($code);
    if ( $code eq '00000000' or $code eq '' ) {
        return '--empty--';
    }
    my @bytes = ();
    for ( my $i=0; $i<8; $i+=2 ) {
        push @bytes, substr $code, $i, 2;
    }
    return join(' ',@bytes);
}


#sub reverse_hex {
#    ($hex) = @_;
#    @bytes = ();
#    for ($i=6; $i>-1; $i-=2) {
#        push @bytes, substr $hex, $i, 2;
#    }
#    $revHex = join ('', @bytes);
#    return $revHex;
#}

#sub hex_to_int {
#    my ( $hex ) = @_;
#    return  unpack ('l',pack 'l', hex($hex));
#}

#sub int_to_hex {
#    my ( $intval ) = @_;
#    $bint = pack("N", $intval);
#    @octets = unpack("C4", $bint);
#    return trim(sprintf "%02X" x 4 . "\n", @octets);
#}

sub HELP_MESSAGE() {
    # write help
    print "\nDistribuce čísla čipu ISIC karty\n";
    print "použití: isic.pl [-p prijmeni] [-j jmeno] [-d datum narozeni] [-w] [-a] [-l]

volby:
    -n NAME - prijmeni studenta
    -s SURNAME - jmeno studenta
    -u USERNAME - login
    -d datum narozeni studenta
    -w se zapisem 
    -a 'all' - najdi vsechny nesrovnalosti
    -l 'long' - podrobný výpis
    -h tento help\n";
}


# *****************
# *    main
# *****************

getopts("n:s:d:u:hwal", \%opt);

if (!%opt) {
    HELP_MESSAGE();
    exit(-1);
}

my $db_baka  = open_sql_bakalari();
my $db_pwk   = open_sql_pwk();
#my $db_safeq = open_sql_safeq();

$fields = "prijmeni, jmeno, rodne_c, datum_nar, trida, isic_karta, isic_cip, isic_plat, isic_objdt, username";
$where = 'where deleted_rc=0';
if (!$opt{'a'}) {
    if ($opt{'n'}) { 
        push @sql_values, $opt{'n'}.'%';
        push @where_cols, 'prijmeni like ?'; 
    }
    if ($opt{'s'}) { 
        push @sql_values, $opt{'s'}.'%';
        push @where_cols, 'jmeno like ?'; 
    }
    if ($opt{'d'}) { 
        push @sql_values, $opt{'d'};
        push @where_cols, 'datum_nar=?'; 
    }
    if ($opt{'u'}) { 
        push @sql_values, $opt{'u'};
        push @where_cols, 'username=?'; 
    }
    $where .= " AND ".join (" AND ", @where_cols);
}   
$sql = "SELECT $fields FROM zaci $where";
#print "SQL: $sql\n";
my $read_bakalari = $db_baka->prepare($sql) or die $db_baka->errstr();
#my $write_dbf = $db_baka->prepare("update $dbf_zaci set isic_karta=?,isic_cip=?  where prijmeni=? and jmeno=? and (datum_nar=? or datum_nar=?)") or die $db_baka->errstr();

$csv_file = [];

$read_bakalari->execute(@sql_values);
while ($data = $read_bakalari->fetchrow_hashref()) {
    my ( $pwk_rec, $pwk_result     ) = get_pwk_data($db_pwk, $data);
#   my ( $safeq_rec, $safeq_result ) = get_safeq_data($db_safeq, $data);
    $safeq_result = 0;   
    if ($opt{'a'}) {
        if ( $pwk_result || $safeq_result ) { 
            print_data ($data, $pwk_rec, $pwk_result, $safeq_rec, $safeq_result, $opt{'l'}); 
        }
    } else {
        print_data ($data, $pwk_rec, $pwk_result, $safeq_rec, $safeq_result, $opt{'l'}); 
    }
    # --- write db ---
    if ( $opt{'w'} ) {
        if ( $pwk_result == 1 ) {
            update_pwk_card($db_pwk, $pwk_rec, $data);
        }           
        if ( $safeq_result == 1 || $safeq_result == 2) {           
#            update_safeq_card($db_safeq, $safeq_rec, $data);
            append_csv($safeq_rec, $data, $csv_file);
        }
    }
}
if ( @$csv_file ) { write_csv($csv_file); }
#$csv_file = [ 'ice;12345678', 'krikrej;22334455', 'bla;12' ];
#write_csv($csv_file); 
print STDERR "\nDone.\n";
