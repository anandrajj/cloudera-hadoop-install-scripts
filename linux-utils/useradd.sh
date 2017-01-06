#!/bin/bash
# Author Anan
# Date March 2015
# Description - Program to turn of firewalls (iptables) and add users in the args with password tempurer#123 and also add them to supergroup to give complete access to hdfs.
#Turnoff firewall
/etc/init.d/iptables save
/etc/init.d/iptables stop
chkconfig iptables off

#add new group supergroup
getent group supergroup | groupadd supergroup
#Setup default password & encrypt using crypt
#password="tempurer#123"
#pass=$(perl -e 'print crypt($ARGV[0], "password")' $password)
#hardcoding the password generated from above step as perl will not be available in the new machine.
pass="pax7l4GRkJbG."

#setup all users passed
for username in "$@"
do
	useradd -m -p $pass $username
	usermod -a -G supergroup $username
done
