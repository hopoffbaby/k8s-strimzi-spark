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

