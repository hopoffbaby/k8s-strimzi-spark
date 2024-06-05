# set up k8s env

using docker desktop, rancher desktop or k3s

## k3s
### install
install k3s

sudo curl -sfL https://get.k3s.io | sh -

### uninstsall

sudo k3s-uninstall.sh

sudo k3s-agent-uninstall.sh

## Docker desktop

### install metrics-server

kubectl apply -f components.yaml


