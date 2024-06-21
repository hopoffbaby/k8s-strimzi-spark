on ubuntu 22.04

`sudo apt update
`
`sudo apt install zfsutils-linux`

`lsblk`

`sudo zpool create mypool /dev/sdb`

`sudo zfs set compression=zstd-3 mypool`

`sudo zfs set dedup=on mypool
`
`sudo zfs create mypool/mydataset`

automatically mounted at /mypool/mydataset

`sudo chmod 777 /mypool/mydataset`

`scp -r f-clnt-241:/bulkdata/mon /mypool/mydataset/`

`sudo zpool list`

`sudo zfs list`

`sudo zpool status`

`sudo zfs get all mypool/mydataset`

`sudo zfs get compressratio mypool/mydataset`

`sudo zpool get dedupratio mypool`

predict dedup and compression performance:
`sudo zdb -S mypool`

use zfs list to get logical size
`zfs list`

use zpool list to get physical size
`zpool list -v`


compare the physical to the logical and get a total data reduction number:

```
watch -d 'echo "scale=2; $(zfs list -o used -H mypool/mydataset | awk '\''{if ($1 ~ /T$/) print substr($1, 1, length($1)-1) * 1024; else if ($1 ~ /G$/) print substr($1, 1, length($1)-1); else if ($1 ~ /M$/) print substr($1, 1, length($1)-1) / 1024}'\'') / $(zpool list -v | awk '\''/sdb/ {if ($3 ~ /T$/) print substr($3, 1, length($3)-1) * 1024; else if ($3 ~ /G$/) print substr($3, 1, length($3)-1); else if ($3 ~ /M$/) print substr($3, 1, length($3)-1) / 1024}'\'')" | bc'
```