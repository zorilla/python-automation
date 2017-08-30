rem Batch file to create python package

set version=1.0.1

rmdir /S /Q package
mkdir package
mkdir package\zorilla
mkdir package\zorilla\data
mkdir package\dist

rem Python and package stuff

copy /Y python\__init__.py package\zorilla
copy /Y python\DESCRIPTION.rst package
copy /Y python\MANIFEST.in package
copy /Y python\README.rst package
copy /Y python\setup.py package

copy /Y python\config.py package\zorilla
copy /Y python\example.py package\zorilla
copy /Y python\backtrace.py package\zorilla
copy /Y python\host.py package\zorilla
copy /Y python\serial_expect.py package\zorilla
copy /Y python\ssh_expect.py package\zorilla
copy /Y config\default.cfg package\zorilla\data
rem python\dos2unix.py package\calient\data\echo_server.py

pushd package
python setup.py sdist --formats zip
pip install dist\zorilla-%version%.zip --upgrade
popd

