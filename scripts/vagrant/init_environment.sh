# Install necessary packages
apt-get update
apt-get install -y git postgresql-server-dev-9.1 python-dev cmake build-essential libgnutls28-dev uuid-dev gnutls-bin memcached

# Set up virtual environment
mkdir -p /var/www/envs
if [ ! -d /var/www/envs/twweb ]; then
    wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py
    python get-pip.py
    pip install virtualenv
    virtualenv /var/www/envs/twweb
    printf "\n\nsource /var/www/twweb/environment_variables.sh\n" >> /var/www/envs/twweb/bin/activate
    cp /var/www/twweb/scripts/vagrant/environment_variables.sh /var/www/twweb/
fi
if [ ! -L /var/www/twweb/bin ]; then
    ln -s /var/www/envs/twweb/bin /var/www/twweb/bin
fi

source /var/www/twweb/environment_variables.sh

# Install Taskd and setup certificates
if [ ! -d $TWWEB_TASKD_DATA ]; then
    # See environment variable TWWEB_TASKD_DATA

    mkdir -p $TWWEB_TASKD_DATA/src
    cd $TWWEB_TASKD_DATA/src

    wget http://taskwarrior.org/download/taskd-1.0.0.tar.gz
    tar xzf taskd-1.0.0.tar.gz
    cd taskd-1.0.0

    which taskd
    if [ $? -ne 0 ]; then
        cmake .
        make
        make install
    fi

    cd $TWWEB_TASKD_DATA
    export TASKDDATA=$TWWEB_TASKD_DATA
    taskd init
    cp /var/www/twweb/scripts/vagrant/simple_taskd_upstart.conf /etc/init/taskd.conf

    service taskd stop

    # generate certificates
    cd $TWWEB_TASKD_DATA/src/taskd-1.0.0/pki
    ./generate
    cp client.cert.pem $TASKDDATA
    cp client.key.pem $TASKDDATA
    cp server.cert.pem $TASKDDATA
    cp server.key.pem $TASKDDATA
    cp server.crl.pem $TASKDDATA
    cp ca.cert.pem $TASKDDATA

    cp /var/www/twweb/scripts/vagrant/simple_taskd_configuration.conf /var/taskd/config
    cp /var/www/twweb/scripts/vagrant/certificate_signing_template.template /var/taskd/cert.template

    service taskd start
fi

which task
if [ $? -ne 0 ]; then
    cd $TWWEB_TASKD_DATA/src
    wget http://taskwarrior.org/download/task-2.3.0.tar.gz
    tar xzf task-2.3.0.tar.gz
    cd task-2.3.0
    cmake .
    make
    make install
fi

# Install requirements
source /var/www/envs/twweb/bin/activate
pip install --download-cache=/tmp/pip_cache -r /var/www/twweb/requirements.txt
