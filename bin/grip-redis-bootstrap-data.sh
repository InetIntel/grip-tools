#!/bin/sh

HOST="[`hostname`]"
START_STR="starting data bootstrap"
END_STR="data bootstrap done"

grip-redis-adjacencies-missing.sh

grip-redis-pfx2as-newcomer-bootstrap.sh

grip-redis-pfx2as-historical-missing.sh
