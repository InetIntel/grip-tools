#!/bin/bash
set -e

# install dependencies
sudo apt-get update
sudo apt-get install -y openjdk-8-jre-headless zookeeperd

sudo update-alternatives --set java /usr/lib/jvm/java-8-openjdk-amd64/jre/bin/java

# silly ubuntu
sudo update-rc.d zookeeperd remove
sudo service zookeeper stop || echo "Zookeeper not running"

# create directories needed
KAFKADIR=/usr/local/kafka
LOGDIR=/var/kafka
sudo mkdir -p $KAFKADIR
sudo mkdir -p $LOGDIR

# get kafka and install it
KAFKA=kafka_2.11-0.11.0.2
wget https://hermes.caida.org/951d9f5cc8084e56b581d924adfac012/public-dist/$KAFKA.tgz
tar zxf $KAFKA.tgz
cd $KAFKA
sudo rm -rf $KAFKADIR/*
sudo mv * $KAFKADIR/
cd ..
rm -r $KAFKA

# create log and pid dirs
sudo mkdir -p /var/run/kafka
sudo mkdir -p /var/log/kafka
