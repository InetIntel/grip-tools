#!/bin/sh
set -e
# this script should be run after an outage to fill in any missing data
grip-announced-pfxs-gen-probe-ips --missing | sort | xargs -t -n 1 -P 6 -r grip-announced-pfxs-gen-probe-ips --input
