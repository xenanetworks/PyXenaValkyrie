
This package implements Python OO API for Xena traffic generator.

Functionality
"""""""""""""
The current version supports the following test flow:
	Build configuration -> Start/Stop traffic -> Get statistics.
Supported operations:
	- Load configuration - reserve ports and load configuration (prt or str)
	- Basic operations - get/set attributes, get/create children
	- Start/Stop - transmit, capture
	- Statistics - ports, streams and packet groups
	- Save configuration (prt or str)
	- Disconnect
The package also support Add/Remove objects so it supports the following test case:
	- Get/set frame
	- Capture

Installation
""""""""""""
pip instsll pyxenamanager

Getting started
"""""""""""""""
Under xenamanager.test.xena_samples you will find some basic samples.
See inside for more info.

Related works
"""""""""""""
The package is partially based on https://github.com/fleitner/XenaPythonLib

Contact
"""""""
Feel free to contact me with any question or feature request at yoram@ignissoft.com
