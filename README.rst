
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

Upgrade from version 0.8.5 to version 0.10 and up
"""""""""""""""""""""""""""""""""""""""""""""""""
Remove the owner parameter from init_xena:
xm = init_xena(api, logger, owner) -> xm = init_xena(api, logger)

Call xm.session.connect with owner parameter just before calling add_chassis:
xm.session.connect(owner)
xm.session.add_chassis(chassis)

Replace logoff with disconnect: 
xm.logoff() -> xm.session.disconnect()

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
