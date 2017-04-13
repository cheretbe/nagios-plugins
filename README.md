Custom Nagios plugins collection (downloaded and self-written)

## Installation
```bash
apt-get install git libconfig-json-perl smartmontools nagios-plugins nagios-nrpe-server
# As user nagios (temporary allow shell via vipw)
git clone https://github.com/cheretbe/nagios-plugins.git
# As root
vi /etc/nagios/nrpe.cfg
# allowed_hosts=127.0.0.1, nagios.rs-kgr.local
# command[check_root]
service nagios-nrpe-server restart
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
/var/lib/nagios/nagios-plugins/check_smart_attributes/check_smart_attributes -dbj /var/lib/nagios/nagios-plugins/custom_check_smartdb.json -d /dev/sda -d /dev/sdb -d /dev/sdc -d /dev/sdd -d /dev/sde -d /dev/sdf -ucfgj /var/lib/nagios/local_smartcfg.json
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

```
# 3000 min = 50 h, 5760 min = 96 h = 4 days
/var/lib/nagios/nagios-plugins/check_burp_backup/check_burp_backup.sh -H bykov -w 3000 -c 5760 -d /mnt/zfs-data/burp/ -p
```

## BackupPC Status
```
visudo
# Allow NRPE process to run BackupPC plugin as backuppc user
nagios  ALL= (backuppc) NOPASSWD: /var/lib/nagios/nagios-plugins/check_backuppc/check_backuppc
/var/lib/nagios/nagios-plugins/check_backuppc/check_backuppc

# Restrict access to the script since it uses passwordless sudo
chown :backuppc /var/lib/nagios/nagios-plugins/check_backuppc/check_backuppc
chmod 750 /var/lib/nagios/nagios-plugins/check_backuppc/check_backuppc

command[check_backuppc]=/usr/bin/sudo -u backuppc /var/lib/nagios/nagios-plugins/check_backuppc/check_backuppc
```
