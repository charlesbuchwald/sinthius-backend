#!/usr/bin/env bash
export PYTHONPATH=$PYTHONPATH:/Volumes/Projects/library/python2.7/dev/lib/python2.7/site-packages
python -m sinthius_octopus.run \
    --port=4000 \
    --nuc_port=4000 \
    --debug=$1 \
    --autoreload=True \
    --master=True