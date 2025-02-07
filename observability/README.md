# Goals

- deploy k3s
- install kube-prometheus-stack
- create Prometheus and AlertManager CRDs
- set up a dummy workload
- create ServiceMonitor, PodMonitor and ScrapeConfig CRDs
- Create PrometheusRule
- Create AlertManagerConfig
- Send email


# Deploy K3s
`sudo curl -sfL https://get.k3s.io | sh -`

copy /etc/rancher/k3s/k3s.yaml to local machine and update IP address

# Prom / alertmgr / grafana

## Install kube-prometheus-stack
```
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

sudo helm repo update

sudo helm install --kubeconfig /etc/rancher/k3s/k3s.yaml neils-stack prometheus-community/kube-prometheus-stack

sudo kubectl --namespace default get all -l "release=neils-stack"

sudo kubectl --namespace default get all
```

## Create Prometheus and AlertManager CRDs

kube-prometheus-stack already deploys a prometheus and alertmanager instances by default

```
sudo kubectl get prometheus --all-namespaces
NAMESPACE   NAME                                    VERSION   DESIRED   READY   RECONCILED   AVAILABLE   AGE
default     neils-stack-kube-prometheu-prometheus   v2.54.1   1         1       True         True        29m

sudo kubectl get alertmanager --all-namespaces
NAMESPACE   NAME                                      VERSION   REPLICAS   READY   RECONCILED   AVAILABLE   AGE
default     neils-stack-kube-prometheu-alertmanager   v0.27.0   1          1       True         True        30m
```

But they do not have proper replicas, uninstall and reinstall the kube-prometheus-stack but with a custom values file

in values.yaml, add ingresses with virtual hostnames for grafana, alertmanager, prometheus. Add entries to windows host files (wildcard not supported):

eg

```
172.26.81.24 alertmanager.d-arc-itd-clt01
172.26.81.24 grafana.d-arc-itd-clt01
172.26.81.24 prometheus.d-arc-itd-clt01
```

set `replicas` to 2 for alertmanager and prometheus. set retention to 336h (14d).

copy kubeconfig to local machine and adjust server name / IP

`helm uninstall --kubeconfig kubeconfig.yaml  neils-stack`

`helm install --kubeconfig kubeconfig.yaml --values values.yaml neils-stack prometheus-community/kube-prometheus-stack`

## set up a dummy workload

deploy a wordpress service with metrics enabled

helm repo add bitnami https://charts.bitnami.com/bitnami

helm repo update

`helm install --kubeconfig kubeconfig.yaml --values wordpress-values.yaml wordpress bitnami/wordpress`

# Logging operator and loki

## Install Loki

helm repo add grafana https://grafana.github.io/helm-charts

helm repo update

helm install --kubeconfig kubeconfig.yaml --values loki-values.yaml loki grafana/loki --version 5.47.2

connect it to Grafana

## install Logging Operator

helm upgrade --kubeconfig kubeconfig.yaml --install --wait --create-namespace --namespace logging logging-operator oci://ghcr.io/kube-logging/helm-charts/logging-operator

kubectl --kubeconfig kubeconfig.yaml -n logging get pods

### create a `logging` resource to set up FluentD shipper and `fluentbitagent` to set up collectors
kubectl --kubeconfig kubeconfig.yaml apply -n loggging -f logging-operator/logging.yaml

kubectl --kubeconfig kubeconfig.yaml apply -n loggging -f logging-operator/fluentbitagent.yaml

### create a `output` to determine where logs will be stored
put it along side the apps to collect logs from, which currently are all in the `default` namespace

kubectl --kubeconfig kubeconfig.yaml apply -n default -f logging-operator/output.yaml

### create a `flow` to specify what resources to scrape and which flow to send it to.

kubectl --kubeconfig kubeconfig.yaml apply -n default -f logging-operator/flow.yaml

kubectl --kubeconfig kubeconfig.yaml -n default get logging-all



