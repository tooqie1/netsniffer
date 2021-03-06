import subprocess
from multiprocessing.pool import ThreadPool
import ipaddress as net
import re
from string import ascii_letters
import time

class Netscanner():

    @staticmethod
    def execute_arp():
        process = subprocess.Popen(["arp", "-a"], stdout=subprocess.PIPE)
        output = str(process.communicate())
        return output

    @staticmethod
    def ping_obj(host):
        process = subprocess.Popen(["ping", "-n", "1", host], stdout=subprocess.PIPE)
        streamdata = process.communicate()
        if not f'Reply from {host}' in str(streamdata):
            return False
        else:
            print(f'Response from {host} received.')
            return True

    @staticmethod
    def identify_mac(rawmac):
        mac = rawmac.rsplit('-', 3)[0].replace('-', '')
        file = 'C:\\Users\\bensk\\PycharmProjects\\dhcpsniffer\\vendor.txt'
        with open(file, encoding='utf-8') as data:
            for line in data:
                if mac.upper() in line:
                    vendor = line.split('\t')[1].replace('\n','')
                    return vendor

    @staticmethod
    def find_arp_ips(dump):
        iplist = []
        findip = re.findall('............... +..-..-..-..-..-..', dump)
        for item in findip:
            clean = item.replace('e\\r\\n', '').replace('r\\n', '').replace('\\n', '').replace('\\', '')
            almostclean = re.findall('.+ ', clean)
            for obj in almostclean:
                ip = obj.replace(' ', '').replace('n', '')
                iplist.append(ip)
        return iplist

    @staticmethod
    def find_arp_macs(dump):
        arpmacs = re.findall('..-..-..-..-..-..', dump)
        stophere = ['ff-ff-ff-ff-ff-ff', '01-00-5e-00-00']
        for badmac in stophere:
            for mac in arpmacs:
                if badmac in mac:
                    return arpmacs[:arpmacs.index(mac)]
        return arpmacs[:len(arpmacs)]

    def arp_dump(self):
        print('\nAnalyzing ARP cache...')
        output = self.execute_arp()
        iplist = self.find_arp_ips(output)
        maclist = self.find_arp_macs(output)
        vendorlist = [self.identify_mac(mac) for mac in maclist]
        x = -1
        for line in maclist:
            x += 1
            time.sleep(0.05)
            print(f'IP {iplist[x]} | MAC {maclist[x].replace("-", ":")} | VENDOR {vendorlist[x]}')

    def get_interface_subnet(self):
        output = self.execute_arp()
        interface = re.search('................ *-', output)[0].replace(':', '').replace(' ', '').replace('-', '')
        for i in ascii_letters:
            interface = interface.replace(i, '')
        interface = interface.rpartition('.')[0] + '.0'
        return interface

    def main(self):
        self.netaddr = input(f'\nPlease enter a Subnet!\n(If none entered, main interface will be used)')
        if self.netaddr == '':
            self.netaddr = self.get_interface_subnet()
            print('Using default.')

        subaddr = input(f'\nPlease enter a Mask!\n(Default mask is CIDR /24)')
        if subaddr == '':
            subaddr = '24'
            print('Using default.')

        print('\nPinging...')
        network = self.netaddr + f'/{subaddr}'
        HOSTLIST = [str(item) for item in net.ip_network(network).hosts()]
        mainproc = ThreadPool(254).imap(self.ping_obj, HOSTLIST)
        for thread in mainproc:
            pass

    def __init__(self):
        try:
            self.main()
            if self.netaddr == self.get_interface_subnet():
                self.arp_dump()
        except Exception as error:
            print(f"\nError!\n({error})")

while True:
    Netscanner()

# use re.search to find subnet of main interface and set that as target subnet
# ask for IP that user is searching for (or a list)
# compare MACs against list of vendors
# map IP variables to MAC variables
# if MAC of Online IPs is found in ARP cache dump output then print (device is online)
# *arp cache must be dumped when the program is run
