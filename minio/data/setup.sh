#!/bin/bash

# install helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# add minio operator repo
helm repo add minio-operator https://operator.min.io --insecure-skip-tls-verify

# download operator (because of firewall)
curl -k -LO https://operator.min.io/helm-releases/operator-5.0.15.tgz

# install operator and turn off STS (some k3s issue???)
sudo helm install --namespace minio-operator --create-namespace operator ./operator-5.0.15.tgz --kubeconfig /etc/rancher/k3s/k3s.yaml --set operator.env[0].name=OPERATOR_STS_ENABLED --set operator.env[0].value="off"

# wait for the operator to become ready
sudo kubectl wait deployment/minio-operator --for=condition=Available --timeout=500s -n minio-operator

# Convert service to NodePort so it can be accessed from Laptops private network with vagrant VM

# Ensure yq is installed
if ! command -v yq &> /dev/null
then
    echo "yq could not be found, installing yq..."
    sudo wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O /usr/bin/yq
    sudo chmod +x /usr/bin/yq
fi

# Get the service YAML
sudo kubectl get svc console -n minio-operator -o yaml > console-service.yaml

# Update the service type to NodePort
yq eval '.spec.type = "NodePort"' -i console-service.yaml

# update the service - TODO - investigate why this doesnt apply in vagrant - race condition?
sudo kubectl apply -f console-service.yaml

# show the JWT to use to access the console

sudo kubectl get secret/console-sa-secret -n minio-operator -o json | jq -r '.data.token' | base64 --decode

# show the port to use
sudo kubectl get svc/console -n minio-operator