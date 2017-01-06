#!/usr/bin/env python
import os
import time
import re
import argparse
import errno
from socket import error as socket_error
from getpass import getpass
import paramiko
import json
import requests
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore",category=DeprecationWarning)
    warnings.filterwarnings("ignore",category=UserWarning)
    import pyrax
 
"""
	Author - Anan
	Date - March 2015
	Description: Given a cluster prefix, list ip-address & host names of the machines in that cluster in /etc/hosts format. 
"""
nova = None

def get_servers(cluster_name=None, host=None):
	servers = nova.servers.list()
	first = True

	for server in servers:
		if re.match("^" + cluster_name.strip() + "\S+", server.name, re.IGNORECASE):
			if first:
				if host:
					out_file = open('host.txt','w')
				print '-' * 113
				padding    = " " * (24 - len("NAME"))				
				print "|\t{0}\t|\t\t\t{1}\t\t\t|{2}{3}|\t{4}\t|".format("IP ADDRESS", "ID", "NAME",padding,"STATUS")
				print '-' * 113
				first = False

			ip_address = server.networks['private'][0]
			serv_id	   = server.id
			name       = server.name
			flavor	   = server.flavor['id']
			status	   = server.status

			padding    = " " * (24 - len(name.strip()))
			print "|{0}\t\t|\t{1}\t|{2}{3}|\t{4}\t|".format(ip_address.strip(), serv_id.strip(), name.strip(),padding,status.strip())
			if host:
				out_file.write(str(ip_address) + '\t' + str(name) + '\n')

	if not first:
		print '-' * 113
	return

def is_host_file(bool=None):
	if bool == "yes":
		return True
	else:
		return False

def main():
    args = process_args()
 
    # instantiate the nova client
    global nova
    pyrax.set_setting('identity_type', os.environ['OS_AUTH_SYSTEM'])
    pyrax.set_default_region(os.environ['OS_REGION_NAME'])
    pyrax.set_credentials(os.environ['OS_USERNAME'], os.environ['OS_PASSWORD'])
    nova = pyrax.cloudservers
    writeout_host = is_host_file(args.hosts.lower())
    get_servers(args.cluster_name, writeout_host)
   

def process_args():
    parser = argparse.ArgumentParser(
        description='Returns the details of a hosts under a cluster & also returns a host file that can be appended to /etc/hosts')
    parser.add_argument(
        '--hosts', '-o', metavar='HOSTS', default='no',
        help='Option to create out file with hosts and respective ip_address to hosts.txt'
             'Default is no')
    parser.add_argument(
        '--cluster_name','-c', metavar='CLUSTER_NAME', default="",
        help='Name of the cluster whose details have to printed on screen & host file has to be created')
    return parser.parse_args()

if __name__ == '__main__':
    requests.packages.urllib3.disable_warnings()
    main()