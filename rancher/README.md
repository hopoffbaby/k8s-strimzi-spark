# Installing K3S
vagrant up to create 2 VMs, with K3S installed on one of them

by default `kubectl describe node vm1` shows capacity and allocatable are equal. 

create a /etc/rancher/k3s/config.yaml file to pass reservations into kubelet:

```
kubelet-arg:
  - "kube-reserved=cpu=500m,memory=1Gi,ephemeral-storage=2Gi"
  - "system-reserved=cpu=500m, memory=1Gi,ephemeral-storage=2Gi"
  - "eviction-hard=memory.available<500Mi,nodefs.available<10%"
```

use the following command to verify kublet has the params set

`sudo kubectl get --raw "/api/v1/nodes/vm1/proxy/configz" | jq`

use `sudo kubectl describe node vm1` to verify that capacity and allocable are not equal.

# create some certs 

* for speed, use the generateCerts.sh script

- ca.key = CA private key
- cacerts.pem = CA root certificate
- tls.key = private key for rancher
- csr.conf = conf file used to generate tls.csr
- tls.csr = the CSR request
- tls.crt = signed certificate for rancher



# Install Rancher Server
[docs](https://ranchermanager.docs.rancher.com/getting-started/installation-and-upgrade/install-upgrade-on-a-kubernetes-cluster#install-the-rancher-helm-chart)

* run `installRancher.sh`

add `10.10.10.11 rancher rancher.vagrant.com` to your windows hosts file (as admin):
```
notepad C:\Windows\System32\drivers\etc\hosts
```

optionally add the CA cert to your trusted root store

go to https://rancher.vagrant.com/dashboard/?setup=admin

create a new password

SIaEGAbbcR69YVoC


# Create an K3s downstream cluster

on vm2, add a hosts entry for `10.10.10.11 rancher.vagrant.com`

install the cacerts.pem file onto vm2

```
sudo scp vm1:/home/vagrant/cacerts.pem /usr/local/share/ca-certificates/cacerts.crt
sudo update-ca-certificates
```

sudo journalctl -u rancher-system-agent

create a new cluster in Rancher GUI. Ensure you select insecure for self signed certs. run the registration command on vm2



DNS entry

Keepalived

HA Proxy

RKE2 template

deploy downstream node

Install longhorn CSI

Install 