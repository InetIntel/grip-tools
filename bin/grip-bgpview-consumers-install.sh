#!/bin/bash
set -e

# TODO: once BGPStream-CAIDA has been broken up into multiple repos, start
# installing only the components we need
bgpview-corsaro-install.sh

PREVDIR=`pwd`
TMPDIR=/tmp/grip-bgpview-installer-tmp
mkdir -p $TMPDIR
cd $TMPDIR

CONTAINER=bgpview-dist
# in case .bashrc hasn't been sourced yet:
. $HOME/.limbo-cred

# PyTimeseries
PKG=pytimeseries-0.2.0
echo "Installing $PKG"
swift download $CONTAINER $PKG.tar.gz
tar zxf $PKG.tar.gz
cd $PKG
sudo python setup.py install
cd ../

#PyBGPView-IO-Kafka
PKG=pybgpview.io.kafka-0.1
echo "Installing $PKG"
swift download $CONTAINER $PKG.tar.gz
tar zxf $PKG.tar.gz
cd $PKG
sudo python setup.py install
cd ../

cd $PREVDIR
