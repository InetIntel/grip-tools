#!/bin/sh
set -e
# find the most recent file in swift
LATEST=`swift list grip-triplets-weekly | sort | tail -1 | cut -d . -f 2`
FIRST=`swift list grip-triplets-weekly | sort | head -1 | cut -d . -f 2`
# the following must not be parallelized!
grip-redis-adjacencies --missing --latest-ts=${LATEST} --first-ts=${FIRST} | xargs -t -n 1 -r grip-redis-adjacencies --timestamp
