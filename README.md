
## Python OO API for Xena Valkyrie traffic generator.

### Functionality
The current version supports the following test flow:

- Load/Build configuration -> Change configuration -> Start/Stop traffic -> Get statistics/capture

Supported operations:

- Login, connect to chassis and reserve ports
- Load existing configuration file
- Build configuration from scratch
- Get/set attributes
- Start/Stop - transmit, capture
- Statistics - ports, streams (end to ends) and TPLDs
- Capture - get captured packets
- Release ports and disconnect

### Migrate from pyxenamanager
- Package renamed from xenamanager to xenavalkyrie
- XenaStreamsStats.statistics['rx']:<br>
  Returns all RX statistics indexed by RX port instead of TPLD object.

### Installation
```
pip install xenavalkyrie
```

### Getting started
Under ```xenavalkyrie.test.xena_samples``` you will find some basic samples.<br>
See inside for more info.

### Documentation
http://pyxenavalkyrie.readthedocs.io/en/latest/

### Usage notes
- Do not create XenaManager manually but use the init_xena factory
- When loading configuration files, first load all files only then manipulate the configuration.

### Related works
The package replaces pyxenamanager - https://github.com/xenadevel/PyXenaManager

### Contact
Feel free to contact me with any question or feature request at yoram@ignissoft.com
