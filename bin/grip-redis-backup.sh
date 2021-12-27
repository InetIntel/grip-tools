#!/bin/sh
set -e

LOCKFILE="/tmp/grip-redis-backup.lock"
if [ -f $LOCKFILE ]; then
    MSG="ERROR: Previous backup script still running"
    echo $MSG >&2
    grip-slackmsg.sh redis-backup $MSG
    exit 0;
fi
touch $LOCKFILE

# load the swift credentials
. /home/bgp/.limbo-cred

DUMPFILE=/var/lib/redis/dump.rdb

CONTAINER=grip-redis
OBJECT=grip-redis-snapshot-`hostname`.rdb
SWIFT_OPTS="--segment-size=1073741824 --segment-container=.$CONTAINER-segments"

# ask redis to dump the DB
echo BGSAVE | redis-cli

# wait a bit before we start checking
sleep 20

# wait for the dump to finish
while true; do
    STATUS="`echo "INFO persistence" | redis-cli | fgrep "rdb_bgsave_in_progress:0" || echo saving`"
    if [ "$STATUS" = "saving" ]; then
        sleep 5
        continue
    fi
    echo "Uploading $DUMPFILE to swift://$CONTAINER/$OBJECT" >&2
    swift upload $SWIFT_OPTS $CONTAINER $DUMPFILE --object-name=$OBJECT
    if [ $? -ne 0 ]; then
        MSG="ERROR: Failed to upload redis dump to swift"
        echo $MSG >&2
        grip-slackmsg.sh redis-backup $MSG
    fi
    break
done

rm $LOCKFILE
