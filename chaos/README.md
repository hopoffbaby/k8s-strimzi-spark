# test chaos mesh on k3s

sudo helm repo add chaos-mesh https://charts.chaos-mesh.org

sudo kubectl create ns chaos-mesh

sudo helm install --kubeconfig /etc/rancher/k3s/k3s.yaml chaos-mesh chaos-mesh/chaos-mesh -n=chaos-mesh --set chaosDaemon.runtime=containerd --set chaosDaemon.socketPath=/run/k3s/containerd/containerd.sock --version 2.6.3

sudo kubectl get all -n chaos-mesh

kubectl apply -f components.yaml

kubectl create token account-cluster-viewer-txknh

kubectl describe secrets account-cluster-viewer-mhaui

# uninstall

sudo helm uninstall chaos-mesh -n chaos-mesh