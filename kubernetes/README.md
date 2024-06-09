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


# K9S - kubernetes TUI

wget https://github.com/derailed/k9s/releases/download/v0.32.4/k9s_linux_amd64.deb
sudo apt install ./k9s_linux_amd64.deb 
k9s