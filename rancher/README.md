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

sudo kubectl get --raw "/api/v1/nodes/vm1/proxy/configz" | jq

use `sudo kubectl describe node vm1` to verify that capacity and allocable are not equal.

# create some certs 
```
sudo apt-get update
sudo apt-get install openssl

#create CA private key
openssl genrsa -out ca.key 4096

#create the root certificate
openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 -out cacerts.pem \
  -subj "/C=US/ST=State/L=City/O=YourOrganization/OU=IT/CN=YourRootCA"

#generate private key for rancher
openssl genrsa -out tls.key 2048


```

create a csr.conf file:

```
[ req ]
default_bits       = 2048
prompt             = no
default_md         = sha256
distinguished_name = dn
req_extensions     = req_ext

[ dn ]
C = GB
ST = YourState
L = YourCity
O = YourOrganization
OU = YourDept
CN = rancher.vagrant.com

[ req_ext ]
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = rancher.vagrant.com
DNS.2 = rancher-cluster.local
```

```
# generate the CSR
openssl req -new -key tls.key -out tls.csr -config csr.conf

#sign the CSR with the CA
openssl x509 -req -in tls.csr -CA cacerts.pem -CAkey ca.key -CAcreateserial -out tls.crt -days 365 -sha256 -extfile csr.conf -extensions req_ext
```


- ca.key = CA private key
- cacerts.pem = CA root certificate
- tls.key = private key for rancher
- csr.conf = conf file used to generate tls.csr
- tls.csr = the CSR request
- tls.crt = signed certificate for rancher

install CA on Ubuntu

```
sudo cp cacerts.pem /usr/local/share/ca-certificates/cacerts.crt
sudo update-ca-certificates
```


# Install Rancher Server
[docs](https://ranchermanager.docs.rancher.com/getting-started/installation-and-upgrade/install-upgrade-on-a-kubernetes-cluster#install-the-rancher-helm-chart)


```
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash


sudo helm repo add rancher-stable https://releases.rancher.com/server-charts/stable --kube-insecure-skip-tls-verify --insecure-skip-tls-verify

sudo kubectl create namespace cattle-system

# upload the certificates

sudo kubectl -n cattle-system create secret tls tls-rancher-ingress \
  --cert=tls.crt \
  --key=tls.key

sudo kubectl -n cattle-system create secret generic tls-ca \
  --from-file=cacerts.pem=./cacerts.pem

sudo helm install rancher rancher-stable/rancher \
  --namespace cattle-system \
  --set hostname=rancher.vagrant.com \
  --set bootstrapPassword=admin \
  --set ingress.tls.source=secret --set privateCA=true --insecure-skip-tls-verify --kubeconfig /etc/rancher/k3s/k3s.yaml

sudo kubectl -n cattle-system rollout status deploy/rancher

```

add `10.10.10.11   rancher.vagrant.com` to your windows hosts file (as admin):
```
notepad C:\Windows\System32\drivers\etc\hosts
```

optionally add the CA cert to your trusted root store

go to https://rancher.vagrant.com:30008/dashboard/?setup=admin

create a new password

uXqQEmgOm7qtZQ5i

# Create an RKE2/K3s downstream cluster

on vm2, add a hosts entry for `rancher.vagrant.com 10.10.10.11`


DNS entry

Keepalived

HA Proxy

RKE2 template

deploy downstream node

Install longhorn CSI

Install 