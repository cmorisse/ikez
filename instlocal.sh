#!/usr/bin/env bash

if [ ! -d "./py27" ]; then
    virtualenv py27
fi
rm -rf ikez.egg-info
py27/bin/pip install --editable src/