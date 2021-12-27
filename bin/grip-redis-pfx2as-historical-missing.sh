#!/bin/sh
set -e

LOCKFILE="/tmp/grip-redis-pfx2as-historical.lock"
if [ -f $LOCKFILE ]; then
    MSG="ERROR: Previous pfx2as-historical bootstrap script still running"
    echo $MSG >&2
    exit 1;
fi
touch $LOCKFILE

# this script is designed to be run either to bootstrap redis,
# or occasionally to ensure there is no data missing in the
# current window
# promote wip data first
grip-redis-pfx2as-historical --promote-wip --clean-wip
for DAY_EPOCH in `grip-redis-pfx2as-historical --missing`; do
  grip-redis-pfx2as-historical-date.sh ${DAY_EPOCH}
done

rm $LOCKFILE
