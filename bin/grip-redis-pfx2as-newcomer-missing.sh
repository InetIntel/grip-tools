#!/bin/sh
set -e
# this script is designed to be run either to bootstrap redis,
# or occasionally to ensure there is no data missing in the
# current window
grip-redis-pfx2as-newcomer --missing | sort -r | xargs -t -n 1 -P 6 -r grip-redis-pfx2as-newcomer --timestamp
