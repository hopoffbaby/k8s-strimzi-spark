# test chaos mesh on k3s

sudo helm repo add chaos-mesh https://charts.chaos-mesh.org

sudo kubectl create ns chaos-mesh

sudo helm install --kubeconfig /etc/rancher/k3s/k3s.yaml chaos-mesh chaos-mesh/chaos-mesh -n=chaos-mesh --set chaosDaemon.runtime=containerd --set chaosDaemon.socketPath=/run/k3s/containerd/containerd.sock --version 2.6.3

sudo kubectl get all -n chaos-mesh

sudo kubectl apply -f components.yaml

sudo kubectl create token account-cluster-viewer-fvvgt

sudo kubectl describe secrets account-cluster-viewer-fvvgt

# uninstall

sudo helm uninstall chaos-mesh -n chaos-mesh