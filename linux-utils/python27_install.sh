#!/bin/bash
#Reference: https://www.digitalocean.com/community/tutorials/how-to-set-up-python-2-7-6-and-3-3-3-on-centos-6-4
yum groupinstall -y 'development tools'
yum install -y zlib-dev openssl-devel sqlite-devel bzip2-devel

wget http://www.python.org/ftp/python/2.7.6/Python-2.7.6.tar.xz
# Let's decode (-d) the XZ encoded tar archive:
xz -d Python-2.7.6.tar.xz

# Now we can perform the extraction:
tar -xvf Python-2.7.6.tar
# Enter the file directory:
cd Python-2.7.6

# Start the configuration (setting the installation directory)
# By default files are installed in /usr/local.
# You can modify the --prefix to modify it (e.g. for $HOME).
./configure --prefix=/usr/local    

# Let's build (compile) the source
# This procedure can take awhile (~a few minutes)
make

# After building everything:
make altinstall

# Example: export PATH="[/path/to/installation]:$PATH"
export PATH="/usr/local/bin:$PATH"

#Cd out of Python-2.7.6
cd..

# Let's download the installation file using wget:
wget --no-check-certificate https://pypi.python.org/packages/source/s/setuptools/setuptools-1.4.2.tar.gz

# Extract the files from the archive:
tar -xvf setuptools-1.4.2.tar.gz

# Enter the extracted directory:
cd setuptools-1.4.2

# Install setuptools using the Python we've installed (2.7.6)
python2.7 setup.py install

#cd out of setuptools
cd ..

#Install pip for 2.7
curl https://bootstrap.pypa.io/get-pip.py | python2.7 -

#Addto bashrc
echo "alias python=/usr/local/bin/python2.7" >> ~/.bashrc
source ~/.bashrc
