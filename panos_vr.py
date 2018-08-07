#!/usr/bin/env python

#  Copyright 2018 ON2IT B.V.
#  Based upon the ansible-pan modules by Palo Alto Networks, inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

DOCUMENTATION = '''
---
module: panos_vr
short_description: add or delete a virtual router, add static routes.
description:
    - Add a virtual router, Delete a virtual router, Add static routes.
author: "Rob Maas (@robm83)"
requirements:
    - pan-python can be obtained from PyPi U(https://pypi.python.org/pypi/pan-python)
note:
    - Based upon the 'ansible-pan' modules.
    - Not extensively tested.
options:
    ip_address:
        description:
            - IP address (or hostname) of PAN-OS device being configured.
        required: true
    username:
        description:
            - Username credentials to use for auth.
        default: "admin"
    password:
        description:
            - Password credentials to use for auth.
        required: true
    vr_name:
        description:
            - Virtual Router name
        required: True
    operation:
        description:
            - Operation, add (vr), del (vr) or addstatic (add static route)
        required: True
        default: add
    sr_name:
        description:
            - Name of the static route
    destination:
        description:
            - Route destination addresses
    nexthop:
        description:
            - Nexthop type, could be ip or vr (next-vr)
        default: ip
    commit:
        description:
            - Commit if changed
        default: true
'''

EXAMPLES = '''
   - name: Delete VR default
      panos_vr:
        ip_address: "pan-vm.westeurope.cloudapp.azure.com"
        username: "admin"
        password: "admin"
        vr_name: "default"
        operation: "del"
        commit: "False"  
    - name: Create VR internal
      panos_vr:
        ip_address: "pan-vm.westeurope.cloudapp.azure.com"
        username: "admin"
        password: "admin"
        vr_name: "internal"
        operation: "add"
        commit: "True"
     - name: Add default route
      panos_vr:
        ip_address: "pan-vm.westeurope.cloudapp.azure.com"
        username: "admin"
        password: "admin"
        vr_name: "internal"
        operation: "addstatic"
        sr_name: "default"
        destination: "0.0.0.0/0"
        nexthop: "1.1.1.1"
        commit: "True"
'''

RETURN='''
# Default return values
'''

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import get_exception

try:
    import pan.xapi
    from pan.xapi import PanXapiError
    HAS_LIB = True
except ImportError:
    HAS_LIB = False

_VR_XPATH = "/config/devices/entry[@name='localhost.localdomain']" +\
            "/network/virtual-router/entry[@name='%s']"

#Add VR
def add_vr(xapi, vr_name):
    vr_xml = [
        '<entry name="%s">',
        '</entry>'
    ]
    vr_xml = (''.join(vr_xml) % vr_name)
    xapi.edit(xpath=_VR_XPATH % vr_name, element=vr_xml)
    return True

#Delete VR
def del_vr(xapi, vr_name):
    xapi.delete(xpath=_VR_XPATH % vr_name)
    return True

#Add static route
def add_static_route(xapi, vr_name, sr_name, destination, nexthop, nexthoptype):
    sr_xml = [
        '<entry name="%s">',
            '<destination>%s</destination>',
            '<nexthop>',
              '%s',
            '</nexthop>',
        '</entry>',
    ]

    if (nexthoptype == "ip"):
        nh_xml = '<ip-address>' + nexthop + '</ip-address>'
    elif (nexthoptype == "vr"):
        nh_xml = '<next-vr>' + nexthop + '</next-vr>'
    else: 
        return False

    sr_xml = (''.join(sr_xml) % (sr_name, destination, nh_xml))
    vr_sr_path = _VR_XPATH % vr_name 
    vr_sr_path += "/routing-table/ip/static-route"    
    xapi.set(xpath=vr_sr_path, element=sr_xml)

    return True

#Check if VR exists
def vr_exists(xapi, vr_name):
    xpath = _VR_XPATH % vr_name
    xapi.get(xpath=xpath)
    router = xapi.element_root.find('.//entry')
    return (router is not None)

def main():
    argument_spec = dict(
        ip_address=dict(required=True),
        password=dict(required=True, no_log=True),
        username=dict(default='admin'),
        vr_name=dict(required=True),
        operation=dict(default='add'), #Could be add or del, addstatic
        sr_name=dict(),
        destination=dict(),
        nexthop=dict(),
        nexthoptype=dict(default='ip'), #Could be ip or vr
        commit=dict(type='bool', default=True)
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)
    if not HAS_LIB:
        module.fail_json(msg='pan-python is required for this module')

    ip_address = module.params['ip_address']
    password = module.params['password']
    username = module.params['username']
    vr_name = module.params['vr_name']
    operation = module.params['operation']
    sr_name = module.params['sr_name']
    destination = module.params['destination']
    nexthop = module.params['nexthop']
    nexthoptype = module.params['nexthoptype']
    commit = module.params['commit']

    xapi = pan.xapi.PanXapi(
        hostname=ip_address,
        api_username=username,
        api_password=password
    )

    changed = False
    vrExists = vr_exists(xapi, vr_name)

    if (operation == "add"):
        if (vrExists):
            module.exit_json(changed=False, msg="VR exists, not changed")
        else:
            try:
                changed = add_vr(xapi, vr_name)
            except PanXapiError:
                exc = get_exception()
                module.fail_json(msg=exc.message)        
    elif (operation == "del"):
        if (not vrExists):
            module.exit_json(changed=False, msg="VR does not exists, not changed")
        else:
            try:
                changed = del_vr(xapi, vr_name)
            except PanXapiError:
                exc = get_exception()
                module.fail_json(msg=exc.message)   
    elif (operation == "addstatic"):
        if (not vrExists):
            module.exit_json(changed=False, msg="VR does not exists, not changed")
        else:
            try:
                changed = add_static_route(xapi, vr_name, sr_name, destination, nexthop, nexthoptype)
                if (not changed):
                    module.exit_json(changed=False, msg="Invalid nexthoptype use, ip or vr")
            except PanXapiError:
                exc = get_exception()
                module.fail_json(msg=exc.message)               
    else:
        module.exit_json(changed=False, msg="Operation not clear, use add, del or addstatic")
        changed = False


    if changed and commit:
        xapi.commit(cmd="<commit></commit>", sync=True, interval=1)

    module.exit_json(changed=changed, msg="yippie ka yee")

if __name__ == '__main__':
    main()
