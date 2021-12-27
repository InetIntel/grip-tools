#!/bin/sh
set -e

DUMPDIR=/var/lib/redis
DUMPFILE=$DUMPDIR/dump.rdb
TMPFILE=$DUMPDIR/grip-redis-snapshot.rdb
CONTAINER=grip-redis
OBJECT=grip-redis-snapshot-`hostname`.rdb

# download backup to tmpfile
swift download $CONTAINER $OBJECT --output=$TMPFILE

# stop redis
sudo service redis stop

# move backup into place
mv $TMPFILE $DUMPFILE

# start redis
sudo service redis start
# wait a little so it at least can respond to our status queries
sleep 20

# wait for redis to start
while true; do
    STATUS="`echo "INFO persistence" | redis-cli | fgrep "loading:0" || echo loading`"
    if [ "$STATUS" = "loading" ]; then
        sleep 5
        continue
    fi
    break
done
