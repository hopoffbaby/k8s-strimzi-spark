# Set PowerShell to stop on all errors
$ErrorActionPreference = 'Stop'

# Add the Helm repositories
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add grafana https://grafana.github.io/helm-charts

# Update Helm repositories to ensure the latest charts are available
helm repo update

# Install the Prometheus monitoring stack using custom values, targeting the "monitoring" namespace, and create the namespace if it doesn't exist.
helm install --kubeconfig kubeconfig.yaml --values kube-prometheus-stack\values.yaml --namespace monitoring --create-namespace neils-stack prometheus-community/kube-prometheus-stack

# Install Loki (a log aggregation system) with custom values, in the "loki" namespace, and create the namespace if necessary
helm install --kubeconfig kubeconfig.yaml --values loki/loki-values.yaml --namespace loki --create-namespace loki grafana/loki --version 5.47.2

# Upgrade (or install if not present) the logging operator in the "logging" namespace, and wait for it to be ready
helm upgrade --kubeconfig kubeconfig.yaml --install --wait --create-namespace --namespace logging logging-operator oci://ghcr.io/kube-logging/helm-charts/logging-operator

# Apply the Logging Operator's logging configuration in the "logging" namespace using kubectl. defining that FluentD will be used
kubectl --kubeconfig kubeconfig.yaml apply -n loggging -f logging-operator/logging.yaml

#Apply Fluent Bit Agent (log processor/collector) configuration in the "logging" namespace using kubectl
kubectl --kubeconfig kubeconfig.yaml apply -n loggging -f logging-operator/fluentbitagent.yaml

###
#Install Wordpress to be used to generate logs and metrics to test logging opeartor and kube-prometheus-stack
###

# Install Wordpress with custom values in the "wordpress" namespace, creating the namespace if it does not exist. Prometheus exporter side car enabled in values
helm install --kubeconfig kubeconfig.yaml --values wordpress-values.yaml --namespace wordpress --create-namespace wordpress bitnami/wordpress

# Apply a servicemonitor resource to specify the Prometheus endpoints that should be scraped.
kubectl --kubeconfig kubeconfig.yaml apply -n wordpress -f kube-prometheus-stack\servicemonitor.yaml

# Apply the Logging Operator's output configuration (destination for logs) in the "wordpress" namespace
kubectl --kubeconfig kubeconfig.yaml apply -n wordpress -f logging-operator/output.yaml

# Apply the Logging Operator's flow configuration (rules for routing logs) in the "wordpress" namespace
kubectl --kubeconfig kubeconfig.yaml apply -n wordpress -f logging-operator/flow.yaml

# connect grafana to Loki with http://loki.loki.svc.cluster.local:3100

# install telegraf to scrape vSphere metrics
helm repo add influxdata https://helm.influxdata.com/

helm upgrade --kubeconfig kubeconfig.yaml --install my-release -f telegraf/values.yaml --namespace telegraf --create-namespace influxdata/telegraf 

kubectl --kubeconfig kubeconfig.yaml apply -n telegraf -f .\telegraf\servicemonitor.yaml

#BACKUP PROMETHEUS DATA
#kubectl --kubeconfig ../../kubeconfig.yaml cp monitoring/prometheus-neils-stack-kube-prometheu-prometheus-0:/prometheus .

#RESTORE PROMETHEUS DATA
# kubectl --kubeconfig kubeconfig.yaml cp .\kube-prometheus-stack\prombackup\. monitoring/prometheus-neils-stack-kube-prometheu-prometheus-0:/prometheus