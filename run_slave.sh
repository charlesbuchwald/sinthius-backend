#!/usr/bin/env bash
export PYTHONPATH=$PYTHONPATH:/Volumes/Projects/library/python2.7/dev/lib/python2.7/site-packages
python -m sinthius_octopus.run \
    --port=$1 \
    --nuc_port=$1 \
    --debug=$2 \
    --autoreload=$3 \
    --master=False