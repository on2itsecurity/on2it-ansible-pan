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
module: panos_int_mgt_profile
short_description: add or delete management profile.
description:
    - Add or delete a management profile
author: "Rob Maas (@robm83)"
requirements:
    - pan-python can be obtained from PyPi U(https://pypi.python.org/pypi/pan-python)
note:
    - Based upon the 'ansible-pan' modules.
    - Not extensively tested.
options:
    http:
        description:
            - Enable HTTP
        default: false
    https:
        description:
            - Enable HTTPS
        default: false
    ssh:
        description:
            - Enable SSH
        default: false
    telnet:
        description:
            - Enable Telnet
        default: false
    ping:
        description:
            - enable Ping
        default: true
    http_ocsp:
        description:
            - enable HTTP OCSP
        default: false
    snmp:
        description:
            - enable SNMP
        default: false
    response_pages:
        description:
            - enable Response Pages
        default: false
    userid:
        description:
            - enable User-ID
        default: false
    userid_syslog_ssl:
        description:
            - enable User-ID Sysog Listener-SSL
        default: false
    userid_syslog_udp:
        description:
            - enable User-ID Sysog Listener-UDP
        default: false
    iplist: 
        description:
            - Allowed IP addressess, seperated by comma
        defailt: none
    name: 
        description:
            - Name of the management profile
        default: Allow_Ping
    operation:
        description:
            - Operation, add or del
        required: True
        default: add
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
'''

RETURN='''
# Default return values
'''

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import get_exception
from ansible.utils.display import Display
display = Display()

try:
    import pan.xapi
    from pan.xapi import PanXapiError
    HAS_LIB = True
except ImportError:
    HAS_LIB = False

_MGT_PRF_XPATH = "/config/devices/entry[@name='localhost.localdomain']" +\
            "/network/profiles/interface-management-profile/entry[@name='%s']"

#Add Interface Management Profile
def add_mgtprf(xapi, mgtprf_name, http, https, http_ocsp, ssh, snmp, userid, userid_syslog_ssl, userid_syslog_udp, ping, response_pages, telnet, iplist):

    #Create IP list

    if len(iplist) > 0:
        ips = iplist.split(',')

        ip_xml = '<permitted-ip>'
        for ip in ips:
            ip_xml += '<entry name="' + ip + '"/>'
        ip_xml += '</permitted-ip>'

    mgtprf_xml = [
        '<entry name="%s">',
            ip_xml,
            '<http>' + http + '</http>',
            '<https>' + https + '</https>',
            '<http-ocsp>' + http_ocsp + '</http-ocsp>',
            '<ssh>' + ssh + '</ssh>',
            '<snmp>' + snmp + '</snmp>',
            '<userid-service>' + userid + '</userid-service>',
            '<userid-syslog-listener-ssl>' + userid_syslog_ssl + '</userid-syslog-listener-ssl>',
            '<userid-syslog-listener-udp>' + userid_syslog_udp + '</userid-syslog-listener-udp>',
            '<ping>' + ping + '</ping>',
            '<response-pages>' + response_pages + '</response-pages>',
            '<telnet>' + telnet + '</telnet>',
        '</entry>'
    ]

    mgtprf_xml = (''.join(mgtprf_xml) % mgtprf_name)
    xapi.edit(xpath=_MGT_PRF_XPATH % mgtprf_name, element=mgtprf_xml)

    return True

#Delete VR
def del_mgtprf(xapi, mgtprf_name):
    xapi.delete(xpath=_MGT_PRF_XPATH % mgtprf_name)
    return True

#Check if management profile exists
def mgtprf_exists(xapi, mgtprf_name):
    xpath = _MGT_PRF_XPATH % mgtprf_name
    xapi.get(xpath=xpath)
    router = xapi.element_root.find('.//entry')
    return (router is not None)

def main():
    argument_spec = dict(
        ip_address=dict(required=True),
        password=dict(required=True, no_log=True),
        username=dict(default='admin'),
        http=dict(type='bool',default=False),
        https=dict(type='bool',default=False),
        telnet=dict(type='bool',default=False),
        ssh=dict(type='bool',default=False),
        ping=dict(type='bool',default=True),
        http_ocsp=dict(type='bool',default=False),
        snmp=dict(type='bool',default=False),
        response_pages=dict(type='bool',default=False),
        userid=dict(type='bool',default=False),
        userid_syslog_ssl=dict(type='bool',default=False),
        userid_syslog_udp=dict(type='bool',default=False),
        iplist=dict(),
        name=dict(required=True),
        operation=dict(default='add'), #Could be add or del
        commit=dict(type='bool', default=True)
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)
    if not HAS_LIB:
        module.fail_json(msg='pan-python is required for this module')

    ip_address = module.params['ip_address']
    password = module.params['password']
    username = module.params['username']
    http = 'yes' if module.params['http'] else 'no'
    https = 'yes' if module.params['https'] else 'no'
    telnet = 'yes' if module.params['telnet'] else 'no'
    ssh = 'yes' if module.params['ssh'] else 'no'
    ping = 'yes' if module.params['ping'] else 'no'
    http_ocsp = 'yes' if module.params['http_ocsp'] else 'no'
    snmp = 'yes' if module.params['snmp'] else 'no'
    response_pages = 'yes' if module.params['response_pages'] else 'no'
    userid = 'yes' if module.params['userid'] else 'no'
    userid_syslog_ssl = 'yes' if module.params['userid_syslog_ssl'] else 'no'
    userid_syslog_udp = 'yes' if module.params['userid_syslog_udp'] else 'no'
    iplist = module.params['iplist']
    name = module.params['name']
    operation = module.params['operation']
    commit = module.params['commit']

    xapi = pan.xapi.PanXapi(
        hostname=ip_address,
        api_username=username,
        api_password=password
    )

    changed = False
    mgtprfExists = mgtprf_exists(xapi, name)

    if (operation == "add"):
        if (mgtprfExists):
            module.exit_json(changed=False, msg="Interface Management Profile exists, not changed")
        else:
            try:
                changed = add_mgtprf(xapi, name, http, https, http_ocsp, ssh, snmp, userid, userid_syslog_ssl, userid_syslog_udp, ping, response_pages, telnet, iplist)
            except PanXapiError:
                exc = get_exception()
                module.fail_json(msg=exc.message)        
    elif (operation == "del"):
        if (not mgtprfExists):
            module.exit_json(changed=False, msg="Interface Management Profile does not exists, not changed")
        else:
            try:
                changed = del_mgtprf(xapi, name)
            except PanXapiError:
                exc = get_exception()
                module.fail_json(msg=exc.message)   
    else:
        module.exit_json(changed=False, msg="Operation not clear, use add or del")
        changed = False

    if changed and commit:
        xapi.commit(cmd="<commit></commit>", sync=True, interval=1)

    module.exit_json(changed=changed, msg="yippie ka yee")

if __name__ == '__main__':
    main()
