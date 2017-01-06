#!/bin/sh
# Author Anan
# Date March 2015
# Description Format & Mount the input drive to given mount folder. Takes parms 1 -> drive to be formatted and 2 -> mount dir location.

#Check only 2 arguments are passed. If not terminate.
if [ "$#" -ne 2 ];then
	echo "There must be 2 arguments only" >&2
	exit 1
fi

#Consider 1st arg as Drive and 2nd one a Mount directory
DRIVE=$1
MOUNT_DIR=$2

#Get the size of the drive to be formatted.
SIZE=`fdisk -l $DRIVE | grep Disk | awk '{print $5}'`
 
echo "Size of the disk to be formatted - $SIZE bytes" 

#Calculate the cylinders in the drive 
CYLINDERS=`echo $SIZE/255/63/512 | bc`
 
echo "Number of cylinders in the disk - $CYLINDERS"

#Partition the wohle disk to single drive. 
sfdisk $DRIVE -uC << EOF 
,$CYLINDERS 
EOF
ONE=1
PART_DRIVE=$DRIVE$ONE
format_cmd="mkfs -t ext3 $PART_DRIVE"
echo "Format compact to be executed $format_cmd"
if $format_cmd;then
	echo "Formatting of disk $DRIVE sucessful"
else
	echo "Formatting of dsik $DRIVE failed. Returning with erro" >&2
	exit 1
fi

mkdir -p $MOUNT_DIR
mnt_cmd="mount $PART_DRIVE $MOUNT_DIR"
echo "Mount command to be executed $mnt_cmd"
if $mnt_cmd; then
	echo "Disk $DRIVE was sucessfully mounted at $MOUNT_DIR"
else
	echo "Mount to $MOUNT_DIR failed" >&2
fi
echo -e $PART_DRIVE'\t'$MOUNT_DIR'\t''ext3\tdefaults,noatime,_netdev,nofail 0 2'  >> /etc/fstab
echo "/etc/fstab updated to retain the mounted disk after reboot."
