#!/bin/bash

TS_CONFIG="kafka -b kafka.rogues.caida.org:9092 -p tsk-production -c bgp.5min"

bgpview-server-kafka \
    --brokers="bgpview-kafka.int.limbo.caida.org:9092" \
    --namespace="bgpview-prod" \
    --pub-channel="grip" \
    --publication-timeout=2400 \
    --timeseries-config="$TS_CONFIG"

