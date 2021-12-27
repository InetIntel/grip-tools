#!/bin/sh
#
# Downloads the latest Announced Prefixes probe IPs file to the current
# directory (and write the name of the downloaded file to stdout).
#
# Requires the swift CLI provided by the python-swiftclient package
# Also requires the python-keystoneclient package for authentication
# e.g.:
# sudo pip install python-swiftclient python-keystoneclient

export OS_PROJECT_NAME=bgp
export OS_USERNAME=s-bgp-ro
#export OS_PASSWORD=
export OS_AUTH_URL=https://auth-limbo.caida.org
export OS_AUTH_VERSION=3

CONTAINER="grip-announced-pfxs-probe-ips"
LATEST_OBJ=`swift list $CONTAINER | tail -1`
FILENAME=`basename $LATEST_OBJ`
swift --quiet download $CONTAINER $LATEST_OBJ --output=$FILENAME
echo $FILENAME
