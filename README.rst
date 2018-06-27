
This package implements Python OO API for Xena traffic generator.

Functionality
"""""""""""""
The current version supports the following test flow:
	Load/Build configuration -> Change configuration -> Start/Stop traffic -> Get statistics/capture
Supported operations:
	- Login, connect to chassis and reserve ports
	- Load existing configuration file
	- Build configuration from scratch
	- Get/set attributes
	- Start/Stop - transmit, capture
	- Statistics - ports, streams (end to ends) and TPLDs
	- Capture - get captured packets
	- Release ports and disconnect

Upgrade from version 0.9.2 to version 1.0.0 and up
""""""""""""""""""""""""""""""""""""""""""""""""""
Version 0.9.2 is the last version supporting only CLI API.
In order to introduce REST API some changes that breaks backwards compatibily were made:
- xena_object.get_attributes() 
  Remove the attribute parameter and return all attributes of the object instead.

Installation
""""""""""""
pip instsll pyxenamanager

Getting started
"""""""""""""""
Under xenamanager.test.xena_samples you will find some basic samples.
See inside for more info.

Documentation
"""""""""""""
http://pyxenamanager.readthedocs.io/en/latest/

Related works
"""""""""""""
The package is partially based on https://github.com/fleitner/XenaPythonLib

Contact
"""""""
Feel free to contact me with any question or feature request at yoram@ignissoft.com
