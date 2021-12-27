#!/usr/bin/env perl
use strict;
use File::Find;

my $SWIFT_CONTAINER_PFX = "grip-"; # e.g., grip-moas
my $PATH_TMPL = "year=%04d/month=%02d/day=%02d/hour=%02d";

if (@ARGV != 1) {
    print STDERR "Usage: $0 tmpdir\n";
    exit -1;
}

my ($tmpdir) = @ARGV;

$SIG{INT}  = \&signal_handler;
my $kill_cnt = 0;

sub signal_handler {
    $kill_cnt++;
}

while (1) {
    # look for .done files
    find(\&do_tmpdir, ($tmpdir));

    sub do_tmpdir()
    {
        if ($kill_cnt) {
            print STDERR "INFO: Caught $kill_cnt INTs, exiting\n";
            exit 0;
        }

	return unless(/\.gz\.done$/);

        my $basename = $_;
        $basename =~ s/\.done$//;
        # NOTE: basename MAY get changed. do not use it to access the local file

        my $absname_done = $File::Find::name;
        my $absname = $absname_done;
        $absname =~ s/\.done$//;

        unless (-f $absname) {
            my $msg = "WARN: done file without data file ($basename)";
            print STDERR "$msg\n";
            return;
        }

        #print STDERR "Archiving $basename to swift\n";

        # what kind of file is this?
        my $consumer;
        my $timestamp;

        # announced-pfxs.1506718080.w86400.gz
        # pfx-origins.1506718080.gz
        # routed-space.1506717960.86400s-window.gz
        # moas.1506716160.0s-window.events.gz
        # subpfx-submoas.1506709380.events.gz
        # subpfx-defcon.1506715740.events.gz
        # edges.1506707160.0s-window.events.gz
        if (/(announced-pfxs)\.(\d+)\.w\d+\.gz/ ||
            /(pfx-origins)\.(\d+)\.gz/ ||
            /(routed-space)\.(\d+)\.\d+s\-window\.gz/ ||
            /(moas)\.(\d+)\.\d+s\-window\.events\.gz/ ||
            /subpfx-(submoas)\.(\d+)\.events\.gz/ ||
            /subpfx-(defcon)\.(\d+)\.events\.gz/ ||
            /(edges)\.(\d+)\.\d+s\-window\.events\.gz/) {
            $consumer = $1;
            $timestamp = $2;

            if ($consumer eq "moas" || $consumer eq "edges") {
                # window is unused, remove from file name
                $basename = "$consumer.$timestamp.events.gz";
            }
        } else {
            my $msg = "WARN: Unrecognized file $basename";
            print STDERR "$msg\n";
            return;
        }

        # parse the timestamp
        my ($sec,$min,$hour,$mday,$mon,$year) = gmtime($timestamp);

        # what container will this go in?
        my $container = $SWIFT_CONTAINER_PFX . $consumer;
        my $segment_container = ".$container-segments";
        # build the object "path"
        my $path = sprintf($PATH_TMPL, $year+1900, $mon+1, $mday, $hour);

        print STDERR "$basename --> $container $path/$basename ";

        my $upload_opts = "--segment-size=1073741824";
        my $seg_opts = "--segment-container=$segment_container";
        my $object = "$path/$basename";
        my $cmd = "swift upload $upload_opts $seg_opts $container $absname --object-name=$object >/dev/null";
        unless ((my $rc = system($cmd)) == 0) {
            my $msg = "WARN: Could not upload $basename to swift ($rc)";
            print STDERR "\n$msg\n";
            if ($rc == 2) {
                # probably someone tried to kill the script
                $kill_cnt++;
            }
            return;
        }

        print STDERR "done\n";

        # announce that this file is now available for further processing
        my $announcement = "swift consumer $consumer $container $object $timestamp";
        my $announce_cmd = "echo \"$announcement\" | grip-announce --announce";
        unless (system($announce_cmd) == 0) {
            my $msg = "ERROR: Could not announce upload of $container/$object";
            print STDERR "$msg\n";
            return;
        }

        # now delete the local file and the corresponding .done file
        unlink $absname_done;
        unlink $absname;
    }

    sleep 5;
}
