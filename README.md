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
