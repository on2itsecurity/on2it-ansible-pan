# Ansible PAN Modules

Additional and/or changed modules for the ansible-pan project <https://github.com/PaloAltoNetworks/ansible-pan/>.

* panos_int_mgt_profile.py - Create/delete a interface management profile
* panos_interface.py - Changed interface module, to allow static IP configuration
* panos_vr.py - Create/delete a virtual router and add static routes

Note: *There is a new updated and more complete interface module available on the ansible-pan page.*

## Installation

* Copy (git clone) the files to your local machine
* Create a symlick to the 'panos_vr' module in your ansible modules directory (MAC: /Library/Python/2.7/site-packages/ansible/modules/network/panos/)

```bash
sudo ln -s /Users/rob/Documents/on2it-ansible-pan/panos_vr.py panos_vr.py
```

* Create a symlick to the 'panos_int_mgt_profile' module in your ansible modules directory
  (MAC: /Library/Python/2.7/site-packages/ansible/modules/network/panos/)

```bash
sudo ln -s /Users/rob/Documents/on2it-ansible-pan/panos_int_mgt_profile.py panos_int_mgt_profile.py
```

* Move the default panos_interface.py to panos_interface.old

```bash
sudo mv panos_interface.py panos_interface.old
```

Create a symlink to the 'panos_interface' module.

```bash
sudo ln -s /Users/rob/Documents/on2it-ansible-pan/panos_interface.py panos_interface.py
```

## Examples

### PAN VR module (panos_vr.py)

```ansible
- name: check if ready
  hosts: localhost
  connection: local
  gather_facts: False
  strategy: debug

  roles:
    - role: PaloAltoNetworks.paloaltonetworks

  tasks:
    - name: Delete VR default
      panos_vr:
        ip_address: "pan-vm.westeurope.cloudapp.azure.com"
        username: "admin"
        password: "secret"
        vr_name: "default"
        operation: "delete"
        commit: "False"  
    - name: Create VR Inside
      panos_vr:
        ip_address: "pan-vm.westeurope.cloudapp.azure.com"
        username: "admin"
        password: "secret"
        vr_name: "inside"
        operation: "add"
        commit: "True"
    - name: Create VR Outside
      panos_vr:
        ip_address: "pan-vm.westeurope.cloudapp.azure.com"
        username: "admin"
        password: "secret"
        vr_name: "outside"
        operations: "add"
        commit: "True"
```

Add static route with IP as next hop

```ansible
  - name: Add default route
      panos_vr:
        ip_address: "pan-vm.westeurope.cloudapp.azure.com"
        username: "admin"
        password: "secret"
        vr_name: "outside"
        operation: "addstatic"
        sr_name: "default"
        destination: "0.0.0.0/0"
        nexthop: "1.1.1.1"
        commit: "True"
```

Add static route with VR as next hop

```ansible
  - name: Add default route
      panos_vr:
        ip_address: "pan-vm.westeurope.cloudapp.azure.com"
        username: "admin"
        password: "secret"
        vr_name: "inside"
        operation: "addstatic"
        sr_name: "default"
        destination: "0.0.0.0/0"
        nexthop: "outside"
        nexthoptype: "vr"
        commit: "True"
```

### PAN Interface module (panos_interface.py)

Configure an interface

```ansible
    - name: Set ethernet1/1
      panos_interface:
        ip_address: "pan-vm.westeurope.cloudapp.azure.com"
        username: "admin"
        password: "secret"
        if_name: "ethernet1/1"
        if_type: "static"
        if_address: "1.2.3.4/24"
        vr_name: "outside"
        zone_name: "outside"
        commit: "False"
```

### PAN Interface Management Profile module (panos_int_mgt_profile.py)

```ansible
    - name: Add management profile
      panos_int_mgt_profile:
        ip_address: "pan-vm.westeurope.cloudapp.azure.com"
        username: "admin"
        password: "secret"
        telnet: False
        http: False
        https: True
        http_ocsp: False
        snmp: False
        ssh: True
        userid: True
        userid_syslog_ssl: False
        userid_syslog_udp: False
        ping: True
        response_pages: True
        iplist: "1.2.3.4/32,5.6.7.8/32"
        name: "allow_management_from_fake_ip"
        operation: "add"
        commit: "False"  
```