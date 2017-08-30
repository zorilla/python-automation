#!/bin/bash
#Batch file to package switchtest files into a self-extracting archive

version="1.0.1"

rm package
rm -rf package
mkdir package
mkdir package/zorilla
mkdir package/zorilla/data
mkdir package/zorilla/discovery
mkdir package/dist


#Python and package stuff
cp -av python/__init__.py package/zorilla
cp -av python/DESCRIPTION.rst package
cp -av python/MANIFEST.in package
cp -av python/README.rst package
cp -av python/config.py package/zorilla
cp -av python/example.py package/zorilla
cp -av python/backtrace.py package/zorilla
cp -av python/host.py package/zorilla
cp -av python/serial_expect.py package/zorilla
cp -av python/ssh_expect.py package/zorilla
cp -av python/default.cfg package/zorilla/data
#cp -av python/dos2unix.py package/zorilla/data/echo_server.py

pushd package
find . -type f -exec dos2unix {} \;
python setup.py sdist
sudo pip install dist/zorillaeng-$version.tar.gz --upgrade
popd

