#!/usr/bin/env python
import os
import time
import re
import argparse
import errno
from socket import error as socket_error
from getpass import getpass
import paramiko
import requests
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore",category=DeprecationWarning)
    warnings.filterwarnings("ignore",category=UserWarning)
    import pyrax

nova = None
'''
	Author - Anan
	Date - March 2015
	Create a Server machine in the RackSpace clould using the API commands. 
'''
def get_flavor(name):
    """
        Given a name get the flavor.
    """
    return nova.flavors.find(name=name)


def get_image(name):
    """
        Get the image details for a given name.
    """
    return nova.images.find(name=name)
 
 
def create_new_server(flavor=None, image=None, key_name=None, name=None, size=100):
    """
        Create new server using the input flavor, image & key name.
    """
    #server = nova.servers.create(name=name, flavor=flavor.id,
    #                             image=image.id, key_name=key_name)
    kwargs = {}
    if flavor.disk == 0:
	block_device_mapping_v2 = [{
             'boot_index': '0',
             'delete_on_termination': True,
             'destination_type': 'volume',
             'uuid': image.id,
             'source_type': 'image',
             'volume_size': str(size),
        }]
	kwargs['block_device_mapping_v2'] = block_device_mapping_v2
	image = None
 
    server = nova.servers.create(name, image, flavor, key_name=key_name, **kwargs)
    
    print 'Building, {0} please wait...'.format(name)

    # wait for server create to be complete
    pyrax.utils.wait_until(server, "status", "ACTIVE", interval=3, attempts=0,verbose=True)
    print 'Building, {0} please wait...'.format(name)

    # wait for server create to be complete
    while server.status == 'BUILD':
        time.sleep(5)
        server = nova.servers.get(server.id)  # refresh server
 
    # check for errors
    if server.status != 'ACTIVE':
        raise RuntimeError('Server did not boot, status=' + server.status)
 
    # the server was assigned IPv4 and IPv6 addresses, locate the IPv4 address
    ip_address = None
    for network in server.networks['public']:
        if re.match('\d+\.\d+\.\d+\.\d+', network):
            ip_address = network
            break
    if ip_address is None:
        raise RuntimeError('No IP address assigned!')
    print 'Server is running at IP address ' + ip_address
    return ip_address
 
 
def run_script(ip_address, script_name):
    """
        Function to run the shell script or command on the newly created server.
    """
    print 'Running Script...'
 
    # establish a SSH connection
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.load_system_host_keys()
    retries_left = 3
    while True:
        try:
            ssh.connect(ip_address, username='root')
            break
        except socket_error as e:
            if e.errno != errno.ECONNREFUSED or retries_left <= 1:
                raise e
        time.sleep(10)  # wait 10 seconds and retry
        retries_left -= 1
 
    # upload deployment script
    ftp = ssh.open_sftp()
    ftp.put(script_name, script_name)
    ftp.chmod(script_name, 0544)
 
    # deploy
    exec_cmd = "./" + script_name
    print "Command that will be executed on Remote Machine: " + exec_cmd
    stdin, stdout, stderr = ssh.exec_command(exec_cmd)
    status = stdout.channel.recv_exit_status()
    open('stdout.log', 'wt').write(stdout.read())
    open('stderr.log', 'wt').write(stderr.read())
    if status != 0:
        raise RuntimeError(
            'Deployment script returned status {0}.'.format(status))
 
 
def process_args():
    parser = argparse.ArgumentParser(
        description='Run an script on the newly Created RackSpace Server')
    parser.add_argument(
        '--flavor', '-f', metavar='FLAVOR', default='1 GB General Purpose v1',
        help='Flavor to use for the instance.'
             'Default is 1 GB General Purpose v1.')
    parser.add_argument(
        '--image', '-i', metavar='IMAGE',
        default='CentOS 6 (PVHVM)',
        help='Image to use for the server. Default is  CentOS 6 (PVHVM)')
    parser.add_argument(
        '--hddsize', '-d', metavar='DISK_SIZE',
        default=100,
        help='Size of the hard drive to be attached.')
    parser.add_argument(
        'key_name', metavar='KEY_NAME',
        help='Keypair name to install on the server. '
             'Must be uploaded to your cloud account in advance.')
    parser.add_argument(
        'script_name', metavar='SCRIPT_NAME',
        help='The boot strap script name to be executed on the newly setup RackSpace Server')
    parser.add_argument(
        'cluster_name', metavar='CLUSTER_NAME',
        help='Name of the cluster. Machines under the cluster will be sequentially named by suffixing numbers.')
    parser.add_argument(
        'cluster_size', metavar='CLUSTER_SIZE',
        help='Number of machines to be created.')
    return parser.parse_args()

def is_number(s):
    """
        Helper function to check if an string is number.
    """
    try:
        int(s)
        return True
    except ValueError:
        return False
 
def main():
    args = process_args()
 
    # instantiate the nova client
    global nova
    pyrax.set_setting('identity_type', os.environ['OS_AUTH_SYSTEM'])
    pyrax.set_default_region(os.environ['OS_REGION_NAME'])
    pyrax.set_credentials(os.environ['OS_USERNAME'], os.environ['OS_PASSWORD'])
    nova = pyrax.cloudservers
 
    flavor = get_flavor(args.flavor)
    image = get_image(args.image)
    
    if not is_number(args.cluster_size):
        raise RuntimeError('cluster_size argument is not Numeric')

    if int(args.cluster_size) <= 0:
        raise RuntimeError('Invalid Cluster Size. It must be greater than zero')

    for i in range(int(args.cluster_size)):
        name = args.cluster_name + "-" + str(i)
        try:
            existing_server = nova.servers.find(name=name)
            server_exists = True
        except Exception as e:
            server_exists = False
        if server_exists:
            print "Server name-{0},id-{1}  already exists. So skipping commisioning".format(existing_server.name, existing_server.id) 
        else: 
            ip_address = create_new_server(flavor, image, args.key_name, name, args.hddsize)
            run_script(ip_address, args.script_name)
            print 'Script now sucessfully run at {0}'.format(ip_address)

if __name__ == '__main__':
        requests.packages.urllib3.disable_warnings()
	main()
