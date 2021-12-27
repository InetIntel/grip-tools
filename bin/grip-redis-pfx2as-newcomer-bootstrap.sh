#!/bin/sh
set -e
# find the most recent file in swift, and load that
LATEST=`swift list grip-pfx-origins | sort | tail -1 | cut -d . -f 2`
grip-redis-pfx2as-newcomer --timestamp=${LATEST}
# remove now outdated data (to keep DB size small)
grip-redis-pfx2as-newcomer --clean
# now fill in any missing data
grip-redis-pfx2as-newcomer-missing.sh
