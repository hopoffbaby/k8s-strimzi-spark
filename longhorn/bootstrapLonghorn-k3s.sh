curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

sudo helm repo add longhorn https://charts.longhorn.io

sudo helm repo update

sudo helm install --kubeconfig /etc/rancher/k3s/k3s.yaml longhorn longhorn/longhorn --namespace longhorn-system --create-namespace --version 1.6.2

sudo kubectl -n longhorn-system get all

firefox http://10.43.197.177:80



#sudo kubectl delete namespace longhorn-system

