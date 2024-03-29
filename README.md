Custom Nagios plugins collection (downloaded and self-written)

## TODO
* https://github.com/HariSekhon/nagios-plugins/blob/master/check_yum.py
* https://serverfault.com/questions/122178/how-can-i-check-from-the-command-line-if-a-reboot-is-required-on-rhel-or-centos/311733#311733
* https://exchange.nagios.org/directory/Plugins/Hardware/Others/check_raspberry_temp/details
* https://exchange.nagios.org/directory/Plugins/Hardware/Server-Hardware/Others/check_rasp_temp/details
* https://exchange.nagios.org/directory/Plugins/Hardware/Others/check_rpi_temperature/details

## Installation
```bash
apt-get install git libconfig-json-perl smartmontools nagios-plugins nagios-nrpe-server python\
  python-tz python-dateutil python-requests python-lxml

# Ubuntu 20.04
apt install git libconfig-json-perl smartmontools monitoring-plugins \
  nagios-nrpe-server python-is-python2 python-tz python-dateutil \
  python-lxml python-idna python-certifi
# There are no python-requests and python-urllib3 packages in 20.04 repos
# Find latest versions for 19.10 at
# https://packages.ubuntu.com/eoan/all/python-requests/download
# https://packages.ubuntu.com/eoan/all/python-urllib3/download
dpkg -i python-urllib3_1.24.1-1ubuntu1_all.deb
dpkg -i python-requests_2.21.0-1_all.deb

# Ubuntu 22.04
apt install git libconfig-json-perl smartmontools monitoring-plugins   nagios-nrpe-server virtualenv python2 python2-pip-whl python2-setuptools-whl

sudo su - nagios -s /bin/bash
virtualenv -p python2 ~/.cache/venv/py2
nano .profile
# Add the following
# export PATH=/var/lib/nagios/.cache/venv/py2/bin:$PATH
# re-login
python -m site
pip install pytz dateutils lxml idna certifi



# As user nagios (temporary allow shell via vipw) in the home dir (/var/lib/nagios, check with pwd)
# git clone https://github.com/cheretbe/nagios-plugins.git
ansible -m ansible.builtin.git -a "repo=https://github.com/cheretbe/nagios-plugins.git dest=/var/lib/nagios/nagios-plugins" --become --become-user nagios linux_nagios_clients
```

#### Auto-update (deprecated)

As root add to sudoers (`visudo`):
```
# Allow update script to restart NRPE service
nagios ALL=NOPASSWD: /usr/sbin/service nagios-nrpe-server stop
nagios ALL=NOPASSWD: /usr/sbin/service nagios-nrpe-server start
```
On server:
```
# Allow update script to restart Nagios service
nagios ALL=NOPASSWD: /usr/sbin/service nagios stop
nagios ALL=NOPASSWD: /usr/sbin/service nagios start
```
![exclamation](https://github.com/cheretbe/notes/blob/master/images/warning_16.png) On server home path is `/home/nagios`, not `/var/lib/nagios`
```bash
# as user nagios

# Don't allow group writing to the directory in order to avoid logrotate skipping
# rotation "because parent directory has insecure permissions"
mkdir -p -m 755 /var/lib/nagios/log
# on server:
mkdir -p -m 755 /home/nagios/log

/var/lib/nagios/nagios-plugins/update/update_nagios_plugins.sh --verbose >>/var/lib/nagios/log/nagios-plugins-update.log
# on server
/home/nagios/nagios-plugins/update/update_nagios_plugins.sh --verbose >>/home/nagios/log/nagios-plugins-update.log

# as root
printf "# Check for repository updates daily\n%02d %02d * * * nagios /var/lib/nagios/nagios-plugins/update/update_nagios_plugins.sh >>/var/lib/nagios/log/nagios-plugins-update.log\n" $((RANDOM % 60)) $((RANDOM % 24)) >/etc/cron.d/nagios-plugins-update
# on server
printf "# Check for repository updates daily\n%02d %02d * * * nagios /home/nagios/nagios-plugins/update/update_nagios_plugins.sh >>/home/nagios/log/nagios-plugins-update.log\n" $((RANDOM % 60)) $((RANDOM % 24)) >/etc/cron.d/nagios-plugins-update

chmod 644 /etc/cron.d/nagios-plugins-update

cat >/etc/logrotate.d/nagios-plugins-update <<EOL
/var/lib/nagios/log/nagios-plugins-update.log {
  monthly
  rotate 3
  size 50M
  compress
  delaycompress
  missingok
  notifempty
  create 644 nagios nagios
}
EOL

# on server
cat >/etc/logrotate.d/nagios-plugins-update <<EOL
/home/nagios/log/nagios-plugins-update.log {
  monthly
  rotate 3
  size 50M
  compress
  delaycompress
  missingok
  notifempty
  create 644 nagios nagios
}
EOL

# Don't allow group writing to the file in order to avoid logrotate skipping
chmod 644 /etc/logrotate.d/nagios-plugins-update
# Check log rotation status
logrotate -d /etc/logrotate.d/nagios-plugins-update
```
* https://www.digitalocean.com/community/tutorials/how-to-manage-log-files-with-logrotate-on-ubuntu-12-10

## Config

`/etc/nagios/nrpe_local.cfg` ~~`/etc/nagios/nrpe.cfg`~~ entry example:
```
command[check_nagios_plugins_update_status]=/var/lib/nagios/nagios-plugins/check_status_file/check_status_file.py /var/lib/nagios/plugins_update_status
```
On server
```
define command{
        command_name check_nagios_plugins_update_status
        command_line /home/nagios/nagios-plugins/check_status_file/check_status_file.py /home/nagios/plugins_update_status
}

# Local
define service{
        use                     local-service
        host_name               localhost
        service_description     Nagios Plugins Update Status
        check_command           check_nagios_plugins_update_status
}

# Remote
define service {
        use                     custom-service
        hostgroup_name          custom-linux-servers
        service_description     Nagios Plugins Update Status
        check_command           check_nrpe!check_nagios_plugins_update_status
}
```

## HDD SMART Attributes

```bash
visudo
# Allow NRPE process access to smart parameters
nagios ALL=(root)NOPASSWD:/usr/sbin/smartctl

# as user nagios
/var/lib/nagios/nagios-plugins/check_smart_attributes/check_smart_attributes -dbj /var/lib/nagios/nagios-plugins/check_smart_attributes/custom/check_smartdb.json -d /dev/sda -d /dev/sdb
```
`/etc/nagios/nrpe.cfg` entry example:
```
command[check_smart]=/var/lib/nagios/nagios-plugins/check_smart_attributes/check_smart_attributes -dbj /var/lib/nagios/nagios-plugins/check_smart_attributes/custom/check_smartdb.json -d /dev/sda -d /dev/sdb
```
More info on critical attributes:
https://en.wikipedia.org/wiki/S.M.A.R.T.#Known_ATA_S.M.A.R.T._attributes

System-local thresholds:
```
cp nagios-plugins/check_smart_attributes/check_smartcfg.json ./local_smartcfg.json
/var/lib/nagios/nagios-plugins/check_smart_attributes/check_smart_attributes -dbj /var/lib/nagios/nagios-plugins/custom_check_smartdb.json -d /dev/sda -d /dev/sdb -d /dev/sdc -d /dev/sdd -d /dev/sde -d /dev/sdf -ucfgj  /etc/nagios/local_smartcfg.json
```
Sample local_smartcfg.json contents
``` json
{
  "Devices" : {
    "/dev/sdc" : {
      "Threshs" : {
        "5" : ["16","19"]
      }
    }
  }
}
```

## ZFS Pool Status

```
visudo
# Allow NRPE process access to ZFS pool status
nagios  ALL=NOPASSWD: /var/lib/nagios/nagios-plugins/check_zpools/check_zpools.sh -p ALL -w 80 -c 90

# Restrict access to the script since it uses passwordless sudo
chmod 700 /var/lib/nagios/nagios-plugins/check_zpools/check_zpools.sh

command[check_zfs_pool]=sudo /var/lib/nagios/nagios-plugins/check_zpools/check_zpools.sh -p ALL -w 80 -c 90
```

## BURP Backups Status

```bash
# 3000 min = 50 h, 5760 min = 96 h = 4 days
/var/lib/nagios/nagios-plugins/check_burp_backup/check_burp_backup.sh -H bykov -w 3000 -c 5760 -d /mnt/zfs-data/burp/ -p
```

## BackupPC Status
```bash
visudo
# Allow NRPE process to run BackupPC plugin as backuppc user
nagios  ALL= (backuppc) NOPASSWD: /var/lib/nagios/nagios-plugins/check_backuppc/check_backuppc
/var/lib/nagios/nagios-plugins/check_backuppc/check_backuppc

# Restrict access to the script since it uses passwordless sudo
chown :backuppc /var/lib/nagios/nagios-plugins/check_backuppc/check_backuppc
chmod 750 /var/lib/nagios/nagios-plugins/check_backuppc/check_backuppc

# command[check_backuppc]=/usr/bin/sudo -u backuppc /var/lib/nagios/nagios-plugins/check_backuppc/check_backuppc
```

## Ubuntu Unattended Upgrades
```bash
#command[check_unattended_upgrades]=/var/lib/nagios/nagios-plugins/check_ubuntu_unattended_upgrades/unattended_upgrades.py
```
Add to `/etc/apt/apt.conf.d/20auto-upgrades`:
```
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
```
