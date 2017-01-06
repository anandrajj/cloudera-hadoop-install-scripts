#!/usr/bin/env python
import os
import sys
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
	Date - March, 2015
	Description - This code serves the purpose of creating virtual machines in the Rackspace cloud. Specifications of the machines are coded in a json file and input to the script.
	Input json is validated for mandatory parms, creates API calls for spinning up servers, validates server created is usable, attaches Harddisks as required and runs external scripts as specified. 
	
	At the end it outputs the ip-address of the machines along with hostnames in /etc/hosts format. 
	
	Sample input json script is in the same folder - vm_spec.json 
	
"""

	
nova = None

 
def get_flavor(name):
    return nova.flavors.find(name=name)
 
 
def get_image(name):
    return nova.images.find(name=name)
 
 
def create_new_server(flavor=None, image=None, key_name=None, name=None,size='100'):
#    not_working_flavors = ['compute', 'memory']
#    exactMatch = re.compile(r'%s' % '|'.join(not_working_flavors), flags=re.IGNORECASE)
#
#    if len(exactMatch.findall(flavor.name)) > 0 :    
#	create_server = 'nova boot --flavor ' + flavor.id + ' --block-device source=image,id=' +  image.id + ',dest=volume,size=' + str(size) + ',shutdown=remove,bootindex=0 ' + name + ' --key-name ' + key_name
#	create_server_out = os.popen(create_server,'r',1)
#	id='none'
#        for line in create_server_out:
#            if re.search(r'\bid\b',line):
#               id = line.split("|")[2].strip()
#               break
#	server = nova.servers.get(id)
#	create_server_out.close()
#
#    else:
#        server = nova.servers.create(name=name, flavor=flavor.id,
#                                 image=image.id, key_name=key_name)

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
    while server.status == 'BUILD':
        time.sleep(5)
        server = nova.servers.get(server.id)  # refresh server
 
    # check for errors
    if server.status != 'ACTIVE':
        raise RuntimeError('Server did not boot, status=' + server.status)

 
    # the server was assigned IPv4 and IPv6 addresses, locate the IPv4 address
    ip_address = None
    for network in server.networks['private']:
        if re.match('\d+\.\d+\.\d+\.\d+', network):
            ip_address = network
            break
    if ip_address is None:
        raise RuntimeError('No IP address assigned!')
    print 'Server is running at IP address ' + ip_address
    return server
 
 
def run_script(ip_address, file_name, exec_cmd="ls"):
    print 'Running Script...'
 
    # establish a SSH connection
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.load_system_host_keys()
    retries_left = 3
    while retries_left > 0:
        try:
            ssh.connect(ip_address, username='root')
            break
        except socket_error as e:
            if e.errno != errno.ECONNREFUSED or retries_left <= 1:
	         print "SSH to remote machine timed-out. Running script fialed."
		 return
#                raise e
        time.sleep(10)  # wait 10 seconds and retry
        retries_left -= 1
 
    # upload deployment script
    ftp = ssh.open_sftp()
    ftp.put(file_name, file_name)
    ftp.chmod(file_name, 0544)
 
    # deploy
    #exec_cmd = "./" + script_name
    print "Command that will be executed on Remote Machine: " + exec_cmd
    stdin, stdout, stderr = ssh.exec_command(exec_cmd)
    status = stdout.channel.recv_exit_status()
    open('stdout.log', 'wt').write(stdout.read())
    open('stderr.log', 'wt').write(stderr.read())

    if status != 0:
        raise RuntimeError(
            'Deployment script returned status {0}.'.format(status))
    else:
	exec_cmd = "rm -f" + file_name
    	print "Command that will be executed on Remote Machine: " + exec_cmd
	stdin, stdout, stderr = ssh.exec_command(exec_cmd)

def validate_input (vmspec):
    vmspec_header = ['name','key_name', 'cluster']
    vmspec_detail = ['flavor', 'image', 'script','suffix','size']

    if len(list(set(list(vmspec)) - set(vmspec_header))) == 0:
        for machine in vmspec['cluster']:
            parm_diff = list(set(vmspec_detail) - set(machine))
            for parm in parm_diff:
                if (parm =='suffix' or parm == 'script'):
                    pass
                else:
                    raise RuntimeError('Error in input vmspec json file. Machines not having all required values or has spurious values --' + str(machine))
    else:
        raise RuntimeError('Error in input vmspec json file. Header is as expected')

    return
 
def is_number(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
 
def main(filename=None):
	# Load json file with specification of virual machines to be created on the rackspace cloud
    vmspec = json.load(open(filename,'r'))
    out_file = open('host.txt','w')

	# Perform validation on the json input for mandatory inputs 
    validate_input(vmspec)

    # instantiate the nova client
    global nova
	
	# Get the rackspace Auth parms to execute the APIs 
    pyrax.set_setting('identity_type', os.environ['OS_AUTH_SYSTEM'])
    pyrax.set_default_region(os.environ['OS_REGION_NAME'])
    pyrax.set_credentials(os.environ['OS_USERNAME'], os.environ['OS_PASSWORD'])
    nova = pyrax.cloudservers  
    cbs  = pyrax.cloud_blockstorage	

    cluster_name = vmspec['name']

    seq = 0
    list_of_server_ip=[]
	#For each detail line in the input json, perform validation steps, create server, validate if server is usable, attach hard disks and execute some custom scripts on the new machines.
    for machine in vmspec['cluster']:
	
        # Get the flavor & Image id of the new machine for the input human readable names. 
	flavor = get_flavor(machine['flavor'])
        image = get_image(machine['image'])

	# Validate if the number of machines parm "size" is a valid numeric value and greater than zero.
        if not is_number(machine['size']):
            raise RuntimeError('cluster_size argument is not Numeric')

        if int(machine['size']) <= 0:
            raise RuntimeError('Invalid Cluster Size. It must be greater than zero')

			
        for i in range(int(machine['size'])):
            seq += 1

            if 'suffix' in machine:
                machine_name = str(cluster_name) + '-' +str(machine['suffix']) + '-' + str(seq)
            else:
                machine_name = str(cluster_name) + '-' + str(seq)

            try:
                server = nova.servers.find(name=machine_name)
                server_exists = True
            except Exception as e:
                server_exists = False
                
            if server_exists:
                print "Server name-{0},id-{1}  already exists. So skipping commisioning".format(server.name, server.id) 
            else: 
                if 'boot-vol-size' in machine:
		    boot_vol_size = machine['boot-vol-size']
		else:
		    boot_vol_size = 100
		    print 'Defaulting boolt volume size to 100 GB. Will be applied only for Compute & Memory flavors'
		
		server_not_all_ok = True
		server_usable={u'rackconnect_automation_feature_manage_software_firewall': u'ENABLED',
                   u'rackconnect_automation_feature_provison_public_ip': u'ENABLED',
                   u'rackconnect_automation_status': u'DEPLOYED',
                   u'rackconnect_automation_feature_configure_network_stack': u'ENABLED'}

		while server_not_all_ok:
		      server = create_new_server(flavor,image, str(vmspec['key_name']), machine_name,boot_vol_size)
		      pyrax.utils.wait_until(server, "metadata", server_usable, interval=3, attempts=100,verbose=True)		      
		      server = nova.servers.get(server.id)	
		      
		      if server.metadata == server_usable:
			 print "Server is all fine. So, proceeding with rest of the steps."
			 server_not_all_ok = False
		      else:
			 print "Server is not usable. So, deleting the server and recreating."
			 server.delete()
			 try:
			    pyrax.utils.wait_until(server, "status", "DELETED", interval=3, attempts=0,verbose=True)
		         except nova.exceptions.NotFound:
                            print "Server deleted..."  

		for network in server.networks['private']:
                   if re.match('\d+\.\d+\.\d+\.\d+', network):
                      ip_address = network
		      break	
	
	       	known_hosts = open("/root/.ssh/known_hosts","r")
		lines = known_hosts.readlines()
		known_hosts.close()
	        
		known_hosts = open("/root/.ssh/known_hosts","w")
		for line in lines:
		    if line.find(ip_address) < 0:
      		       known_hosts.write(line)
		known_hosts.close()       

		
		
		
		if 'hdfs-vol' in machine:
		    for each_vol_detail in machine['hdfs-vol']:
			if ('hdfs-vol-name' in each_vol_detail and 'mountpoint' in each_vol_detail and 'mountdir' in each_vol_detail):
			      if 'hdfs-vol-type' in each_vol_detail:
			     	  if (each_vol_detail['hdfs-vol-type'] == 'SSD' or each_vol_detail['hdfs-vol-type'] == 'SATA'):
			       		hdfs_vol_type  = each_vol_detail['hdfs-vol-type']
			   	  else:
			       		hdfs_vol_type = 'SATA'
			       		print 'Assuming default type of HDFS Volume as SATA'	
			      else:
			          print 'Assuming default type of HDFS Volume as SATA'
			          hdfs_vol_type = 'SATA'

			      if 'hdfs-vol-size' not in each_vol_detail:
			          hdfs_vol_size = 1024 
			          print 'hdfs-vol-size not found, Defaulting hdfs volume size to 1 TB'
			      elif int(each_vol_detail['hdfs-vol-size']) > 1024:
			          hdfs_vol_size = 1024
			          print 'Max volume size allowed is 1 TB. Defaulting hdfs volume size to 1024 GB'	
			      elif int(each_vol_detail['hdfs-vol-size']) < 101:
				  hdfs_vol_size = 110
				  print 'Volume size must be greater than 100. Defaulting hdfs volume to 110 GB'
			      else:
			          hdfs_vol_size = int(each_vol_detail['hdfs-vol-size'])
				
			      hdfs_vol_name = server.name + "-" + str(each_vol_detail['hdfs-vol-name'])
			      vol = cbs.create(name=hdfs_vol_name, size=hdfs_vol_size, volume_type=hdfs_vol_type)
			      pyrax.utils.wait_until(vol, "status", "available", interval=3, attempts=0,verbose=True)
			      vol.attach_to_instance(server, mountpoint=each_vol_detail['mountpoint'])
			      pyrax.utils.wait_until(vol, "status", "in-use", interval=3, attempts=0,verbose=True)
			      print "Volume %s created and attached to %s server." % (vol.name, server.name)
			      print "Running the Disk formatting script...."
			      disk_format_cmd="./disk-prep.sh" + " " + each_vol_detail['mountpoint'] + " " + each_vol_detail['mountdir'] + " " + "&"
	
		   	      for network in server.networks['private']:
                                  if re.match('\d+\.\d+\.\d+\.\d+', network):
                        	     ip_address = network
                                     run_script(ip_address, "disk-prep.sh", disk_format_cmd)
                                     print 'Disk formating Script now sucessfully run at {0} for disk {1}'.format(server.name, each_vol_detail['hdfs-vol-name'] )
                                     break
			else:
			    print "Skipping one of the hdfs volume creation for server {0} as all mandatory parms hdfs-vol-name, monuntpoint and mountdir are not passed"
            
            if 'script' in machine:
                for network in server.networks['private']:
                    if re.match('\d+\.\d+\.\d+\.\d+', network):
                        ip_address = network
			break

		for each_script in machine['script']:
		    if 'name' in each_script and 'cmd' in each_script:
		        print 'Script will be run at' + ip_address
                       	run_script(ip_address, str(each_script['name']), str(each_script['cmd']))
                       	print 'Script now sucessfully run at {0}'.format(ip_address)
		    else:
			print 'Skipping execution of sciprt as all mandatory script and command not passed'	
            
            for private_ip in server.networks['private']:
                if re.match('\d+\.\d+\.\d+\.\d+', private_ip):
                   out_file.write(str(private_ip) + '\t' + str(server.name) + '\n')
		   list_of_server_ip.append(private_ip)
    
    out_file.close()
    if len(list_of_server_ip) > 0:
	update_host_out = os.popen("cat /etc/hosts > /etc/hosts.bak;cat host.txt >> /etc/hosts")
    for ip in list_of_server_ip:
	run_script(ip, "host.txt", "cat /etc/hosts > /etc/hosts.bak;cat host.txt >> /etc/hosts")

if __name__ == '__main__':
    requests.packages.urllib3.disable_warnings()
    main(sys.argv[1])
