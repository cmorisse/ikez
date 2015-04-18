#!/usr/bin/env bash

# create a eggs_cache directory used by makeit.sh in offline mode
# You must run

if [ ! -d "./py27" ]; then
    echo "You must launch 'instlocal.sh' first"
    exit 1
fi

mkdir -p eggs_cache
py27/bin/pip install -I --download=eggs_cache colorama==0.3.3
py27/bin/pip install -I --download=eggs_cache semver==2.0.1
py27/bin/pip install -I --download=eggs_cache python_dateutil==2.4.2
py27/bin/pip install -I --download=eggs_cache pudb

exit 0