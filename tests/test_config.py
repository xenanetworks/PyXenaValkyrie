
live_demo = '176.22.65.114'
dev_chassis = '176.22.65.117'
localhost = 'localhost'

live_demo_socket = f'{live_demo}:22611'
dev_chassis_socket = f'{dev_chassis}:22611'
live_demo_rest = f'{live_demo}:57911'
dev_chassis_rest = f'{dev_chassis}:57911'

server_properties = {'live_demo_socket': {'server': live_demo_socket,
                                          'locations': [f'{live_demo}/2/4', f'{live_demo}/2/5']},
                     'dev_chassis_socket': {'server': dev_chassis_socket,
                                            'locations': [f'{dev_chassis}/0/0', f'{dev_chassis}/0/1']},
                     'live_demo_rest': {'server': live_demo_rest,
                                        'locations': [f'{live_demo}/2/4', f'{live_demo}/2/5']},
                     'dev_chassis_rest': {'server': dev_chassis_rest,
                                          'locations': [f'{dev_chassis}/0/0', f'{dev_chassis}/0/1']}}

# Default for options.
api = ['rest']
server = ['live_demo_rest']
