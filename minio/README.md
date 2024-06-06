# Install MinIO operator

## Install with Helm

```
helm repo add minio-operator https://operator.min.io

helm install --namespace minio-operator --create-namespace operator minio-operator/operator

kubectl get all -n minio-operator
```

Get secret JWT:
On Linux
```
kubectl get secret/console-sa-secret -n minio-operator -o json | jq -r ".data.token" | base64 -d
```
on windows
```
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String((kubectl get secret/console-sa-secret -n minio-operator -o json | ConvertFrom-Json).data.token))
```

Get access to the operator console:

```
kubectl port-forward svc/console -n minio-operator 9090:9090
```

Open `localhost:9090` and log in with JWT

# Create a MinIO Tenant (cluster)

Create a tenant from the GUI or CLI with the krew command, and then caputre the yaml CRD for it. We will use YAML in the future

In the Configure tab add the extra environment variables for bucket notifications to kafka

https://min.io/docs/minio/linux/administration/monitoring/publish-events-to-kafka.html#minio-bucket-notifications-publish-kafka

```
export MINIO_NOTIFY_KAFKA_ENABLE_PRIMARY="on"
export MINIO_NOTIFY_KAFKA_BROKERS_PRIMARY="my-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092"
export MINIO_NOTIFY_KAFKA_TOPIC_PRIMARY="minio"
```

this needs to be base64 encoded to be added to a secret:

[Convert]::ToBase64String([System.IO.File]::ReadAllBytes(".\config.env")) > base64.txt

get initial user

UUYf9Ykc9V4O4zGO
LtbjYJ9vpVXQAColkQu83lgMFO4zPOui

get the tenant and the yaml for it

```
kubectl get tenant -n minio-operator -o yaml
```

This is saved in this repo as `minio-tenant.yaml`

delete the cluster from the operator GUI, and deploy it from yaml:

kubectl apply -f minio-tenant.yaml -n minio-operator



kubectl apply -f secrets.yaml -n minio-operator
kubectl apply -f minio-tenant.yaml -n minio-operator

env is getting through, but keep getting error about empty tenant credentials...


# DirectPV Vagrant testing

deploy VMs with K3S using vagrant

$env:VAGRANT_EXPERIMENTAL='disks'; vagrant up    

vagrant ssh vm1

/vagrant_data/setup.sh

on laptop:

http://10.10.10.11:<nodeport>

use the node port and jwt displayed by the script to log on
