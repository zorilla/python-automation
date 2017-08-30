# python-automation
Zorilla Python automation

This is a python module that provides control of network hosts and serial devices with an simple expect-like interface.

This module also illustrates:

* How to setup and create a python package on both Windows and Linux
* How to implement a configuration file that matches command line parameters
* Automatic creation of default configuration on first run in the users home directory
* How to implement a logging system

Libraries

* host.py - Generic IP host with SSH support 
* ssh_expect.py - Platform independent expect-like behaviour over SSH 
* serial_expect.py - Platform independent expect-like behaviour over RS-232

Scripts

* package.bat - Create/install the zorilla package for Windows
* package.sh - Create/install the zorilla package for Linux
* example.py - Example script
* backtrace.py - Run gdb backtrace on a running process including tasks
