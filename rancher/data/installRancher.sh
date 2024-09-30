# install helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# add the rancher repo
sudo helm repo add rancher-stable https://releases.rancher.com/server-charts/stable --kube-insecure-skip-tls-verify --insecure-skip-tls-verify

# Create the namespace
sudo kubectl create namespace cattle-system

# upload the certificates
sudo kubectl -n cattle-system create secret tls tls-rancher-ingress \
  --cert=tls.crt \
  --key=tls.key

# create a secret from the CA root cert
sudo kubectl -n cattle-system create secret generic tls-ca \
  --from-file=cacerts.pem=./cacerts.pem

# Install rancher server
sudo helm install rancher rancher-stable/rancher \
  --namespace cattle-system \
  --set hostname=rancher.vagrant.com \
  --set bootstrapPassword=admin \
  --set ingress.tls.source=secret --set privateCA=true --insecure-skip-tls-verify --kubeconfig /etc/rancher/k3s/k3s.yaml

# Wait until its finished installing
sudo kubectl -n cattle-system rollout status deploy/rancher