Custom Nagios plugins collection (downloaded and self-written)

## Installation
```
apt-get install git libconfig-json-perl smartmontools nagios-plugins nagios-nrpe-server
# As user nagios (temporary allow shell via vipw)
git clone https://git.beercaps.ru:50003/orlov/nagios-plugins.git
# As root
vi /etc/nagios/nrpe.cfg
# allowed_hosts=127.0.0.1, nagios.rs-kgr.local
# command[check_root]
service nagios-nrpe-server restart
```

## HDD SMART Attributes

```
visudo
# Allow NRPE process access to smart parameters
nagios ALL=(root)NOPASSWD:/usr/sbin/smartctl

/var/lib/nagios/nagios-plugins/check_smart_attributes/check_smart_attributes -dbj /var/lib/nagios/nagios-plugins/custom_check_smartdb.json -d /dev/sda -d /dev/sdb -d /dev/sdc -d /dev/sdd -d /dev/sde -d /dev/sdf
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

command[check_zfs_pool]=sudo /var/lib/nagios/nagios-plugins/check_zpools/check_zpools.sh -p ALL -w 80 -c 90
```

## BURP Backups Status

```
# 3000 min = 50 h, 5760 min = 96 h = 4 days
/var/lib/nagios/nagios-plugins/check_burp_backup/check_burp_backup.sh -H bykov -w 3000 -c 5760 -d /mnt/zfs-data/burp/ -p
```