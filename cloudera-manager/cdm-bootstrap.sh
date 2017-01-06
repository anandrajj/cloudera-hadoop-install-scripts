#!/bin/bash
#Author - Anand
#Date - March 2015
#Description - Script to Automate the installation of packages required in the Cloudera Manager node. It Installs python rackspace client, Sets up Auth Parameters, turns of firewalls, installs java, setsup cloudera repo and installs cloudera-manager-server and its dependencies. 
STRING="Cloudera Manager Bootstrap Starting...."
echo $STRING
#Install Python 2.7 as it is required for pyrax, wheras centos 6.4 comes with default Python 2.6 
./python27_install.sh
yum -y install gcc python-devel python-netifaces python-pip vim tmux
pip install -U netifaces
pip install -U oslo.config
pip install -U python-novaclient
pip install -U pyrax
pip install -U paramiko
pip install -U python-swiftclient swiftly
pip install -U importlib
#pip install -U os-networksv2-python-novaclient-ext==0.24 os-virtual-interfacesv2-python-novaclient-ext==0.18 python-novaclient==2.21.0 #https://github.com/rackspace/pyrax/issues/542
pip install --upgrade distribute
curl https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py | python -


#2. Upload Credentials for rackspace nova client to ~/.bash_profile
cat >> ~/.bash_profile <<EOL
OS_AUTH_URL=https://identity.api.rackspacecloud.com/v2.0/
OS_VERSION=2.0
OS_AUTH_SYSTEM=rackspace
OS_REGION_NAME=ORD
OS_SERVICE_NAME=cloudserversOpenStack
OS_TENANT_NAME=951282
OS_USERNAME=tspdevdatasci
OS_PASSWORD=b7dc384896a6498fbd403989991cd7a9
OS_NO_CACHE=1
export OS_AUTH_URL OS_VERSION OS_AUTH_SYSTEM OS_REGION_NAME OS_SERVICE_NAME OS_TENANT_NAME OS_USERNAME OS_PASSWORD \
OS_NO_CACHE
EOL

source ~/.bash_profile

cat >> ~/.novarc <<EOL
OS_AUTH_URL=https://identity.api.rackspacecloud.com/v2.0/
OS_VERSION=2.0
OS_AUTH_SYSTEM=rackspace
OS_REGION_NAME=ORD
OS_SERVICE_NAME=cloudserversOpenStack
OS_TENANT_NAME=951282
OS_USERNAME=tspdevdatasci
OS_PASSWORD=b7dc384896a6498fbd403989991cd7a9
OS_NO_CACHE=1
export OS_AUTH_URL OS_VERSION OS_AUTH_SYSTEM OS_REGION_NAME OS_SERVICE_NAME OS_TENANT_NAME OS_USERNAME OS_PASSWORD \
OS_NO_CACHE
EOL
source ~/.novarc

#Generate private & public-key pairs
ssh-keygen -f id_rsa -t rsa -N ''
nova keypair-add --pub-key /root/.ssh/id_rsa.pub vm-create-key #Add the generated publickey to nova.
touch /root/.ssh/known_hosts

#4. Disable Firewall so that cloudera manager can be access via port 7182 in browser.
/etc/init.d/iptables save
/etc/init.d/iptables stop
chkconfig iptables off

#4A.Setup Cloudera Manager Repo
wget -P /etc/yum.repos.d/ http://archive.cloudera.com/cm5/redhat/6/x86_64/cm/cloudera-manager.repo

#5. Install Java
yum -y install oracle-j2sdk1.7

#6. Install Cloudera Manager
yum -y install cloudera-manager-server-db-2

#7. Display cloudera manager service status
service cloudera-scm-server-db start
service cloudera-scm-server start
service cloudera-scm-server status
STRING="Bootstrap completed. Please reboot the system to start the cloudera manager server"
