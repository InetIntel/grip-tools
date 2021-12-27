#!/bin/sh
set -e
DAY_EPOCH=$1
INTERVAL=300
BATCH_INTERVAL=86400

if [ -z ${DAY_EPOCH} ]; then
  echo "Usage: $0 day-epoch"
  exit 255
fi

echo "Executing parallel insertion for $DAY_EPOCH" >&2

perl -e 'while ($offset < '${BATCH_INTERVAL}') { $now = '${DAY_EPOCH}'+$offset; $offset+='${INTERVAL}'; print "$now\n" }' | \
  xargs -n 1 -P 12 -r grip-redis-pfx2as-historical --timestamp

echo "Executing promotion of WIP data into main DB for $DAY_EPOCH"

grip-redis-pfx2as-historical --promote --clean --clean-wip
