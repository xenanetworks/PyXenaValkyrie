
live_demo = '176.22.65.114'
dev_chassis = '176.22.65.117'

dev_chassis_socket = '176.22.65.114:22611'

server_properties = {'dev_chassis_socket': {'server': dev_chassis_socket,
                                            'locations': [f'{dev_chassis}/0/0', f'{dev_chassis}/0/1']}}

# Default for options.
api = ['rest']
server = ['dev_chassis_socket']
