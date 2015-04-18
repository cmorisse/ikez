#!/usr/bin/env bash

# By default, to optimize build speed, all eggs are cached.
# Comment next line to force package installation from pypi
#export ONLINE_MODE="True"

# uncomment next line to embed pudb in generated script
#export EMBED_PUDB="True"

# clean
rm -rf zip_build_temp
rm -rf release

mkdir zip_build_temp
cp src/ikez.py zip_build_temp/__main__.py
cp src/postgresql.py zip_build_temp/
cp src/system_info.py zip_build_temp/
cp src/system.py zip_build_temp/
cp src/odoo.py zip_build_temp/
cp src/utils.py zip_build_temp/


if [ -n "$ONLINE_MODE" ]; then
    # Online version
    py27/bin/pip install -t zip_build_temp/ colorama==0.3.3
    py27/bin/pip install -t zip_build_temp/ semver==2.0.1
    py27/bin/pip install -t zip_build_temp/ python_dateutil==2.4.2
    #if [ "$EMBED_PUDB"  == "True" ]; then
    if [ -n "$EMBED_PUDB" ]; then
        py27/bin/pip install -t zip_build_temp/ pudb
    fi
else
    # Offline, cached version (launch setup_download_cache.sh before)
    # Reference:
    #   http://stackoverflow.com/questions/4806448/how-do-i-install-from-a-local-cache-with-pip
    #
    if [ ! -d "./eggs_cache/" ]; then
        echo "You must launch setup_download_cache.sh before launching this script"
        exit 1
    fi
    py27/bin/pip install --no-index --find-links ./eggs_cache/ -t zip_build_temp/ colorama==0.3.3
    py27/bin/pip install --no-index --find-links ./eggs_cache/ -t zip_build_temp/ semver==2.0.1
    py27/bin/pip install --no-index --find-links ./eggs_cache/ -t zip_build_temp/ python_dateutil==2.4.2
    if [ "$EMBED_PUDB"  == "True" ]; then
        py27/bin/pip install --no-index --find-links ./eggs_cache/ -t zip_build_temp/ pudb
    fi

fi

# add other packages here
rm -rf zip_build_temp/*.egg-info

# make zip containing dev files AND dependencies packages
cd zip_build_temp
zip -r9 ../ikez.zip *
cd ..

# transform zip into an executable
echo '#!/usr/bin/env python' | cat - ikez.zip > ikez
rm ikez.zip
chmod +x ikez
mkdir -p release
mv ikez release/

echo ""
echo "You can use release/ikez or copy it to a folder on your system path."
echo ""
