# Set PowerShell to stop on all errors
$ErrorActionPreference = 'Stop'

helm repo add chaos-mesh https://charts.chaos-mesh.org

helm repo update

kubectl create ns chaos-mesh

helm install chaos-mesh chaos-mesh/chaos-mesh -n=chaos-mesh --version 2.6.3 --set controllerManager.leaderElection.enabled=false

kubectl get all --namespace chaos-mesh

kubectl apply -f rbac.yaml

kubectl create token account-cluster-manager-gqlav


#kubectl port-forward svc/chaos-dashboard -n chaos-mesh 8080:2333

#kubectl apply -f rback.yaml
#kubectl create token account-cluster-manager-gqlav

#kubectl describe serviceaccount account-cluster-manager-gqlav

# use name account-cluster-manager-gqlav and the generated token in the output to logon to chaos mesh

# new experiment > kubernetes > pod fault > pod failure

#make sure experiment name doesnt have spaces

# kind: PodChaos
# apiVersion: chaos-mesh.org/v1alpha1
# metadata:
#   namespace: minio-tenant-source
#   name: minio
# spec:
#   selector:
#     namespaces:
#       - minio-tenant-source
#     labelSelectors:
#       apps.kubernetes.io/pod-index: '0'
#   mode: all
#   action: pod-failure



