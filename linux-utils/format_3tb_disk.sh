#!/bin/bash
# Author Anan
# Date March 2015
# Description - Script to prepare multiple hard disks in single system of size > 3 TB. It uses the parted tool to create partition table and formats the partitions to ext4.
# Reference: 
#			http://www.cyberciti.biz/tips/fdisk-unable-to-create-partition-greater-2tb.html
#			http://rainbow.chard.org/2013/01/30/how-to-align-partitions-for-best-performance-using-parted/
count=1
GREEN='\033[0;32m'
NC='\033[0m'
for disk in "$@"; do
	drive=$disk$count
	mount_folder=/mnt/hdfs$count
	printf "${GREEN}Processing disk $disk${NC}\n"
	parted --script $disk print
	parted --script $disk mklabel gpt
	parted --script $disk unit TB
	parted --script $disk mkpart primary 2048s 100%
	parted --script $disk align-check optimal 1
	parted --script $disk print
	printf "${GREEN}Created partition table for $disk${NC}\n"
	printf "${GREEN}Formating the $drive to ext4${NC}\n"
	mkfs.ext4 $drive
	printf "${GREEN}Creating $mount_folder${NC}\n"
	mkdir $mount_folder
	printf "${GREEN}Mounting the $drive to $mount_folder${NC}\n"
	mount $drive $mount_folder
	printf "${GREEN}Text for /etc/fstab${NC}\n"
	echo -e "$drive\\t$mount_folder\\text4\\tdefaults,noatime\\t1 2"
done