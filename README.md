# Install Strimzi

## Install operator
Install strimzi operator

kubectl apply -f .\kafka-persistent-single.yaml -n kafka


kubectl get pod -n kafka --watch

Or

kubectl wait kafka/my-cluster --for=condition=Ready --timeout=300s -n kafka 

## Produce messages

IN TERMINAL 1

kubectl -n kafka run kafka-producer -ti --image=quay.io/strimzi/kafka:0.40.0-kafka-3.7.0 --rm=true --restart=Never -- bin/kafka-console-producer.sh --bootstrap-server my-cluster-kafka-bootstrap:9092 --topic my-topic

## Consume messages

IN TERMINAL 2

kubectl -n kafka run kafka-consumer -ti --image=quay.io/strimzi/kafka:0.40.0-kafka-3.7.0 --rm=true --restart=Never -- bin/kafka-console-consumer.sh --bootstrap-server my-cluster-kafka-bootstrap:9092 --topic my-topic --from-beginning

## Install Kafka UI

Install kafka-ui using helm and the repo values.yaml file

helm repo add kafka-ui https://provectus.github.io/kafka-ui-charts

helm install kafka-ui kafka-ui/kafka-ui --set envs.config.KAFKA_CLUSTERS_0_NAME=local --set envs.config.KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS=my-cluster-kafka-bootstrap:9092

kubectl port-forward svc/kafka-ui 8080:80

open browser

# Spark 

## Install Spark Operator

https://medium.com/@SaphE/deploying-apache-spark-on-kubernetes-using-helm-charts-simplified-cluster-management-and-ee5e4f2264fd

https://github.com/kubeflow/spark-operator/tree/master


```
helm repo add spark-operator https://kubeflow.github.io/spark-operator

helm repo update

helm install my-release spark-operator/spark-operator --namespace spark-operator --create-namespace --set webhook.enable=true 

NAME: my-release
LAST DEPLOYED: Mon May  6 16:03:02 2024
NAMESPACE: spark-operator
STATUS: deployed
REVISION: 1                                                                                             -operator --create-namespace --set webhook.enable=true 
TEST SUITE: None

helm status --namespace spark-operator my-release

```

## Run a job

Submit the spark job from this repo

```
kubectl apply -f .\spark\spark-pi.yaml

kubectl describe sparkapplication --namespace=spark-operator
```

```
  Warning  Failed       21s (x5 over 102s)  kubelet, docker-desktop  Error: ImagePullBackOff
  Normal   Pulling      7s (x4 over 103s)   kubelet, docker-desktop  Pulling image "gcr.io/spark-operator/spark:v3.1.1"
  Warning  Failed       6s (x4 over 102s)   kubelet, docker-desktop  Failed to pull image "gcr.io/spark-operator/spark:v3.1.1": Error response from daemon: manifest for gcr.io/spark-operator/spark:v3.1.1 not found: manifest unknown: Failed to fetch "v3.1.1" from request "/v2/spark-operator/spark/manifests/v3.1.1".
  Warning  Failed       6s (x4 over 102s)   kubelet, docker-desktop  Error: ErrImagePull

```

