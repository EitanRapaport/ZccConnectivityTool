#!/usr/bin/env python
import os, socket, struct
import sys
from subprocess import PIPE,Popen,check_output
import re

failed = {'Cloud' : {'Ping' : [], 'Telnet': []} , 'Customer' : {'Ping': [], 'Telnet': []}}
nic = check_output(
'iptables-save | grep -i "a pre" | grep -o "eth[0,1]"',
shell=True)
nic = nic.split()
ips = check_output(
'iptables-save | grep -i "a pre" | grep -E -o "([0-9]{1,3}[\.]){3}[0-9]{1,3}"',
shell=True)
ips = ips.split()
ports = check_output(
    'iptables-save | grep -E -i "^-a pre" | grep -o -P "[4,9]...$"',
    shell=True)
ports = ports.split()
#print('count of ips: ' , len(ips))
if len(sys.argv) == 1:
    num_of_pings = 10
else:
    num_of_pings = int(sys.argv[1])
index = 0
ping_timeout = '-w 1'

address_dict = {'Cloud':{'ZVM': None, 'VRAs': []} , 'Customer' : {'ZVM': None, 'VRAs': []}}
for i in range(len(ips)):
    if nic[i] == 'eth1':
        if ips[i] not in address_dict['Cloud']['VRAs'] and address_dict['Cloud']['ZVM'] != ips[i]:
            if ports[i] == '9081':
                address_dict['Cloud']['ZVM']=(ips[i])
            else:
                address_dict['Cloud']['VRAs'].append(ips[i])
    else:
        if ips[i] not in address_dict['Customer']['VRAs'] and address_dict['Customer']['ZVM'] != ips[i]:
            if ports[i] == '9081':
                address_dict['Customer']['ZVM']=(ips[i])
            else:
                address_dict['Customer']['VRAs'].append(ips[i])



address_dict['Cloud']['VRAs'].sort()
address_dict['Customer']['VRAs'].sort()
type(address_dict['Cloud']['VRAs'])

print("\nCloud ZVM IP: " + str(address_dict['Cloud']['ZVM']))
print("Customer ZVM IP: " + str(address_dict['Customer']['ZVM'] ))

print("\n{2:>20}\n{0:32}{1}\n".format("Customer","Cloud","VRAs:"))
for customer,cloud in map(None,address_dict['Cloud']['VRAs'],address_dict['Customer']['VRAs']):
    if customer == None:
        print("{0:30s}{1}".format("",cloud))
    elif cloud == None:
        print(str(customer))
    else:
        print("{0:30s}{1}".format(customer,cloud))


print("\n")

ping_failures = {}

def get_default_gateway_linux():
    with open("/proc/net/route") as fh:
        for line in fh:
             fields = line.strip().split()
             if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                 continue
             return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))

gateway = get_default_gateway_linux()


def ping(ip, component, count):
    if count == 0:
        pass
    else:
        if component == "VRA":
            print("=======")
            sys.stdout.flush()
        response = Popen(['ping','-c',str(count),ping_timeout,ip],stdout=PIPE,stderr=PIPE)
        stdout, stderr = response.communicate()
        packetloss = float(
            [x for x in stdout.decode('utf-8').split('\n') if x.find('packet loss'
            ) != -1][0].split('%')[0].split(' ')[-1])

        if int(packetloss) != 0:
            print("Ping "+ component + " " + ip + " failed")
            if ip in address_dict['Customer']['VRAs'] or address_dict['Customer']['ZVM'] == ip:
                failed['Customer']['Ping'].append(ip)
            elif ip in address_dict['Cloud']['VRAs'] or address_dict['Cloud']['ZVM'] == ip:
                failed['Cloud']['Ping'].append(ip)
            sys.stdout.flush()
        else:
            print("Ping " + component + " " + ip + " success!")
            sys.stdout.flush()
        print("Packet loss was " + str(packetloss) + "%")


def zvm_connectivity(ip):
    ping(ip, "ZVM",num_of_pings)
    telnet = os.system("stdbuf -o 0 -e 0 nc -w 1 -z " + ip + " 9081")
    if telnet == 0:
        print("Telnet ZVM " + ip + " on port 9081 success!")
        sys.stdout.flush()
    else:
        print("Telnet ZVM " + ip + " on port 9081 failed")
        if ip == address_dict['Customer']['ZVM']:
            failed['Customer']['Telnet'].append(ip + " port 9081")
        elif ip == address_dict['Cloud']['ZVM']:
            failed['Cloud']['Telnet'].append(ip + " port 9081")
        sys.stdout.flush()
    print("=======")
    sys.stdout.flush()


def vra_connectivity(ip):
    ports = ["4007", "4008"]
    ping(ip,"VRA",num_of_pings)
    for port in ports:
        telnet = os.system("stdbuf -o 0 -e 0 nc -w 1 -z " + ip + " " + port)
        if telnet == 0:
            print("Telnet VRA " + ip + " over port " + str(port) + " success!")
            sys.stdout.flush()
        else:
            print("Telnet VRA " + ip + " over port " + str(port) + " failed")
            if ip in address_dict['Customer']['VRAs']:
                failed['Customer']['Telnet'].append(ip +  " port " + port)
            elif ip in address_dict['Cloud']['VRAs']:
                failed['Cloud']['Telnet'].append(ip +  " port " + port)
            sys.stdout.flush()


print("Customer facing gateway is: " + gateway)
ping(gateway,"Gateway",num_of_pings)
print("")

### Iterate over the list of IPs and test it according to the
### matching port in the ports list
for ip in ips:
    #print(index)
    if ports[index] == '4008':
        index += 1
        continue
    #print(ip , " is at index ", index, " and the port is ", ports[index])
    if index <= len(ips) - 1:
        if ports[index] == '9081':
            zvm_connectivity(ip)
            index += 1
        else:
            vra_connectivity(ip)
            index = index + 1
    else:
        break
"""
if failed['Customer']['Ping'] != [] or failed['Cloud']['Ping'] != []:
    print("\nFailed Pings:")
    if failed['Customer']['Ping'] != []:
        print("    Customer site:\n")
        for i in failed['Customer']['Ping']:
            print(i)
    if failed['Cloud']['Ping'] != []:
        print("\n    Cloud site:\n")
        for i in failed['Cloud']['Ping']:
            print(i)

if failed['Customer']['Telnet'] != [] or failed['Cloud']['Telnet'] != []:
    print("\nFailed telnets: ")
    if failed['Customer']['Telnet'] != []:
        print("    Customer site:\n")
        for i in failed['Customer']['Telnet']:
            print(i)
    if failed['Cloud']['Telnet'] != []:
        print("\n    Cloud site:\n")
        for i in failed['Cloud']['Telnet']:
            print(i)
"""
"""
print("\n{2:>30}\n   {0:25}{1}".format("Customer","Cloud","Telnet failures:"))
for customer,cloud in map(None, failed['Customer']['Telnet'],failed['Cloud']['Telnet']):
    if customer == None:
        print("{0:30s}{1}".format("",cloud))
        #print("                            " + str(cloud))
    elif cloud == None:
        print(str(customer))
    else:
        print("{0:30s}{1}".format(customer,cloud))
        #print(str(customer) + "    " + str(cloud))

print("\n{2:>30}\n   {0:25}{1}".format("Customer","Cloud","Ping failures:"))
for customer,cloud in map(None, failed['Customer']['Ping'],failed['Cloud']['Ping']):
    if customer == None:
        print("{0:30s}{1}".format("",cloud))
        #print("                            " + str(cloud))
    elif cloud == None:
        print(str(customer))
    else:
        print("{0:30s}{1}".format(customer,cloud))
        #print(str(customer) + "    " + str(cloud))"""

### Print the failed pings and telnets
def print_failures(feature):
    ## Remove duplicates:
    failed['Customer'][feature] = list(set(failed['Customer'][feature]))
    failed['Customer'][feature].sort()
    failed['Cloud'][feature] = list(set(failed['Cloud'][feature]))
    failed['Cloud'][feature].sort()
    ## Print headers
    print("\n{2:>30}\n{0:30}{1}".format("Customer","Cloud",feature +" failures:"))
    ## Go through the lists and print in table:
    for customer,cloud in map(None, failed['Customer'][feature],failed['Cloud'][feature]):
        if customer == None:
            print("{0:30s}{1}".format("",cloud))
        elif cloud == None:
            print(str(customer))
        else:
            print("{0:30s}{1}".format(customer,cloud))

print_failures("Telnet")
print_failures("Ping")

print("")        
iptables = check_output('iptables-save | grep -i "a prerouting"',shell=True)
iptables = iptables.split(b'\n')
for i in iptables:
    print(i)

pretty_table = check_output('/zerto-scripts/table.sh --pretty',shell=True)
pretty_table = pretty_table.split(b'\n')
for i in pretty_table:
    print(i)



print("###End###")
