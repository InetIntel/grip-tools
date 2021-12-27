#!/bin/bash
set -e

# Monkey around with some linux settings that redis wants
echo vm.overcommit_memory=1 | sudo tee -a /etc/sysctl.conf
sudo sysctl vm.overcommit_memory=1
sudo apt install -y hugepages
sudo hugeadm --thp-never

# Redis server deps
sudo apt install -y build-essential tcl

PREVDIR=`pwd`
TMPDIR=/tmp/grip-redis-installer-tmp
mkdir -p $TMPDIR
cd $TMPDIR

# Install redis
wget http://download.redis.io/redis-stable.tar.gz
tar zxf redis-stable.tar.gz
cd redis-stable
make
#make test
sudo make install
cd ../

# Create redis data directory
REDIS_DIR=/var/lib/redis
sudo mkdir -p $REDIS_DIR
sudo chown -R bgp:bgp $REDIS_DIR
sudo chmod 770 $REDIS_DIR

cd $PREVDIR
sudo rm -rf $TMPDIR
