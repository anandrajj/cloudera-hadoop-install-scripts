#!/usr/bin/env python
import os
import sys
import re
import argparse
import requests
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=UserWarning)
    import pyrax

"""
	Author Anan
	Date March 2015
	Description: Given a prefix, gets the list of virtual machines starting with that prefix & deletes them
"""

NOVA = None

def get_servers(cluster_name=None, host=None):
    servers = NOVA.servers.list()
    first = True
    out_list = []

    for server in servers:
        cluster_name.strip()
        if re.match("^" + cluster_name.strip() + "\S+", server.name, re.IGNORECASE):
            if first:
                if host:
                    out_file = open('host.txt', 'w')
                print '-' * 113
                padding = " " * (24 - len("NAME"))
                print "|\t{0}\t|\t\t\t{1}\t\t\t|{2}{3}|\t{4}\t|".format(  \
                    "IP ADDRESS", "ID", "NAME", padding, "STATUS")
                print '-' * 113
                first = False

	    if 'private' in server.networks:
               ip_address = server.networks['private'][0]
	    else:
               ip_address = "0.0.0"
            serv_id = server.id
            name = server.name
            status = server.status
            out_list.append(server)
            padding = " " * (24 - len(name.strip()))
            print "|{0}\t\t|\t{1}\t|{2}{3}|\t{4}\t|".format( \
                ip_address.strip(), serv_id.strip(), \
                name.strip(), padding, status.strip())
            if host:
                out_file.write(str(ip_address) + '\t' + str(name) + '\n')

    if not first:
        print '-' * 113

    return out_list

def wait_for_empty_list(cluster_name=None):
    servers = NOVA.servers.list()
    out_list = []

    for server in servers:
        cluster_name.strip()
        if re.match("^" + cluster_name.strip() + "\S+", server.name, re.IGNORECASE): 
	    out_list.append(server)

    return len(out_list)	


def host_del(del_list=None):
    for server in del_list:
        print "Deleting Server -" + server.name + "..."
        server.delete()

def vol_del(vol_list=None):
    print "Deleteing all volumes which are not attached any of the servers."
    for vol in vol_list:
	if len(vol.attachments) == 0:
	   print "Deleteing unattached volume " + vol.display_name + " with id " + vol.id
	   vol.delete()
	   while len(cbs.findall(id=vol.id)) > 0:
	         print "Deleteing...."

def confirm(prompt=None, resp=False):
    """prompts for yes or no response from the user. Returns True for yes and
    False for no.

    'resp' should be set to the default value assumed by the caller when
    user simply types ENTER.

    >>> confirm(prompt='Create Directory?', resp=True)
    Create Directory? [y]|n:
    True
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y:
    False
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y: y
    True

    """

    if prompt is None:
        prompt = 'Confirm'

    if resp:
        prompt = '%s [%s]|%s: ' % (prompt, 'y', 'n')
    else:
        prompt = '%s [%s]|%s: ' % (prompt, 'n', 'y')

    while True:
        ans = raw_input(prompt)
        if not ans:
            return resp
        if ans not in ['y', 'Y', 'n', 'N']:
            print 'please enter y or n.'
            continue
        if ans == 'y' or ans == 'Y':
            return True
        if ans == 'n' or ans == 'N':
            return False

def main():

    args = process_args()

    # instantiate the NOVA client
    global NOVA, cbs
    pyrax.set_setting('identity_type', os.environ['OS_AUTH_SYSTEM'])
    pyrax.set_default_region(os.environ['OS_REGION_NAME'])
    pyrax.set_credentials(os.environ['OS_USERNAME'], os.environ['OS_PASSWORD'])
    NOVA = pyrax.cloudservers
    cbs = pyrax.cloud_blockstorage

    delete_list = get_servers(args.cluster_name, False)
    

    if len(delete_list) > 0:
        delete = confirm("Dlete the above displayed Machine. Confirm?", False)
        if delete:
            host_del(delete_list)
	    servers_left=wait_for_empty_list(args.cluster_name)
	    print "Deleteing Cluster " + str(args.cluster_name) + ". Please Wait....",
	    while servers_left > 0:
		print '.',
		sys.stdout.flush()
                servers_left=wait_for_empty_list(args.cluster_name)
	    print "Done"
        else:
            print "Exiting without Delete..."

    vol_list = cbs.findall()
    vol_del(vol_list)

def process_args():
    parser = argparse.ArgumentParser(
        description='Displays hosts under a cluster & deletes'\
            	' them on confirmation')
    parser.add_argument(
        'cluster_name', metavar='CLUSTER_NAME',
        help='Name of the cluster to be dleted. If single host to'
             ' be delete provide complete Name.')
    return parser.parse_args()

if __name__ == '__main__':
    requests.packages.urllib3.disable_warnings()
    main()
