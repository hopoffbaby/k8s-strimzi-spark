# Set PowerShell to stop on all errors
$ErrorActionPreference = 'Stop'

# Configuring kubectl to use docker-desktop context
kubectl config set-context docker-desktop
kubectl config use-context docker-desktop

# Create a namespace for the operations
kubectl create namespace test-ns

# Create a service account named 'spark' within the created namespace
kubectl create serviceaccount spark --namespace test-ns

# Create a cluster role binding for the 'spark' service account
kubectl create clusterrolebinding spark-role --clusterrole=edit --serviceaccount=test-ns:spark --namespace=test-ns

# Add the Spark operator Helm repository
helm repo add spark-operator https://kubeflow.github.io/spark-operator

# Update Helm repository to ensure you get the latest charts
helm repo update

# Install the Spark operator in a new namespace with specified configurations
helm install my-release spark-operator/spark-operator --namespace spark-operator --create-namespace `
    --set webhook.enable=true `
    --set sparkJobNamespace=test-ns `
    --set enableBatchScheduler=true `
    --set enableResourceQuotaEnforcement=true

# Output a completion message
Write-Host "Spark operator has been successfully deployed on Kubernetes."
