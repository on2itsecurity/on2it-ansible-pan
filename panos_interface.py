#!/usr/bin/env python

#  Copyright 2018 ON2IT B.V. 
#
#  This is a modified version of the original panos_interface by 
#  Palo Alto Networks.
#  Copyright 2016 Palo Alto Networks, Inc  
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
module: panos_interface
short_description: configure data-port network interface for DHCP or Static
description:
    - Configure data-port interface
author: "Luigi Mori (@jtschichold), Ivan Bojer (@ivanbojer), Rob Maas (@robm83)"
version_added: "2.3"
requirements:
    - pan-python can be obtained from PyPi U(https://pypi.python.org/pypi/pan-python)
note:
    - Checkmode is not supported.
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
    if_name:
        description:
            - Name of the interface to configure.
        required: true
    if_type: 
        description:
            - Type of interface static or dhcp
        required: false
        default: "dhcp"
    if_address:
        description:
            - IP address, when using if_type static
        required: false
    vr_name:
        description:
            - Virtual router to use
        required: false
        default: "default"
    zone_name:
        description:
            - Name of the zone for the interface. If the zone does not exist it is created but if the zone exists and it is not of the layer3 type the operation will fail.
        required: true
    create_default_route:
        description:
            - Whether or not to add default route with router learned via DHCP.
        default: "false"
    commit:
        description:
            - Commit if changed
        default: true
'''

EXAMPLES = '''
- name: enable DHCP client on ethernet1/1 in zone public
  interface:
    ip_address: "pan-vm.westeurope.cloudapp.azure.com"
    username: "admin"
    password: "admin"
    ip_address: "192.168.1.1"
    if_name: "ethernet1/1"
    zone_name: "public"
    create_default_route: "yes"
- name: Add static IP to ethernet1/1 in zone internal
  panos_interface:
    ip_address: "pan-vm.westeurope.cloudapp.azure.com"
    username: "admin"
    password: "secret"
    if_name: "ethernet1/1"
    if_type: "static"
    if_address: "6.6.6.6/24"
    vr_name: "outside"
    zone_name: "outside"
    commit: "False"
'''

RETURN='''
# Default return values
'''

ANSIBLE_METADATA = {'metadata_version': '1.1',
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

_IF_XPATH = "/config/devices/entry[@name='localhost.localdomain']" +\
            "/network/interface/ethernet/entry[@name='%s']"

_ZONE_XPATH = "/config/devices/entry[@name='localhost.localdomain']" +\
              "/vsys/entry/zone/entry"
_ZONE_XPATH_QUERY = _ZONE_XPATH+"[network/layer3/member/text()='%s']"
_ZONE_XPATH_IF = _ZONE_XPATH+"[@name='%s']/network/layer3/member[text()='%s']"
_VR_XPATH = "/config/devices/entry[@name='localhost.localdomain']" +\
            "/network/virtual-router/entry"


def add_if(xapi, if_name, if_type, if_address, vr_name, zone_name, create_default_route):
    if_xml = [
        '<entry name="%s">',
        '<layer3>',
        '%s',
        '</layer3>',
        '</entry>'
    ]

    if (if_type == "dhcp"):
        cdr = 'yes'
        if not create_default_route:
            cdr = 'no'

        if_ip = '<dhcp-client><create-default-route>' + cdr + '</create-default-route></dhcp-client>'
    elif (if_type == "static"):
        if_ip = '<ip><entry name="' + if_address + '"/></ip>'
    else:
        return False

    if_xml = (''.join(if_xml)) % (if_name, if_ip)
    xapi.edit(xpath=_IF_XPATH % if_name, element=if_xml)

    xapi.set(xpath=_ZONE_XPATH+"[@name='%s']/network/layer3" % zone_name,
             element='<member>%s</member>' % if_name)
    xapi.set(xpath=_VR_XPATH+"[@name='" + vr_name + "']/interface",
             element='<member>%s</member>' % if_name)

    return True


def if_exists(xapi, if_name):
    xpath = _IF_XPATH % if_name
    xapi.get(xpath=xpath)
    network = xapi.element_root.find('.//layer3')
    return (network is not None)


def main():
    argument_spec = dict(
        ip_address=dict(required=True),
        password=dict(required=True, no_log=True),
        username=dict(default='admin'),
        if_name=dict(required=True),
        if_type=dict(default='dhcp'), #dhcp or static
        if_address=dict(),
        vr_name=dict(default='default'),
        zone_name=dict(required=True),
        create_default_route=dict(type='bool', default=False),
        commit=dict(type='bool', default=True)
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)
    if not HAS_LIB:
        module.fail_json(msg='pan-python is required for this module')

    ip_address = module.params["ip_address"]
    password = module.params["password"]
    username = module.params['username']

    xapi = pan.xapi.PanXapi(
        hostname=ip_address,
        api_username=username,
        api_password=password
    )

    if_name = module.params['if_name']
    if_type = module.params['if_type']
    if_address = module.params['if_address']
    vr_name = module.params['vr_name']
    zone_name = module.params['zone_name']
    create_default_route = module.params['create_default_route']
    commit = module.params['commit']

    ifexists = if_exists(xapi, if_name)

    if ifexists:
        module.exit_json(changed=False, msg="interface exists, not changed")

    try:
        changed = add_if(xapi, if_name, if_type, if_address, vr_name, zone_name, create_default_route)
        if (not changed):
            module.exit_json(changed=False, msg="Invalid interface type (if_type), use static of dhcp")
    except PanXapiError:
        exc = get_exception()
        module.fail_json(msg=exc.message)

    if changed and commit:
        xapi.commit(cmd="<commit></commit>", sync=True, interval=1)

    module.exit_json(changed=changed, msg="okey dokey")

if __name__ == '__main__':
    main()