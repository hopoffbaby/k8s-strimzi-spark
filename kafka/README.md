# Install Strimzi

## Install operator
Install strimzi operator

```
sudo kubectl create namespace kafka

sudo kubectl create -f 'https://strimzi.io/install/latest?namespace=kafka' -n kafka

```

wait for it to be ready 

```
# kubectl wait deployment/strimzi-cluster-operator --for=condition=Ready --timeout=300s -n kafka

sudo kubectl get pod -n kafka --watch

sudo kubectl logs deployment/strimzi-cluster-operator -n kafka -f
```

## deploy a kafka instance

```
sudo kubectl apply -f kafka-persistent-single.yaml -n kafka
sudo kubectl wait kafka/my-cluster --for=condition=Ready --timeout=300s -n kafka 
```

# Test producing / consuming

## Produce messages

IN TERMINAL 1

```
sudo kubectl -n kafka run kafka-producer -ti --image=quay.io/strimzi/kafka:0.40.0-kafka-3.7.0 --rm=true --restart=Never -- bin/kafka-console-producer.sh --bootstrap-server my-cluster-kafka-bootstrap:9092 --topic my-topic
```

## Consume messages

IN TERMINAL 2

```
sudo kubectl -n kafka run kafka-consumer -ti --image=quay.io/strimzi/kafka:0.40.0-kafka-3.7.0 --rm=true --restart=Never -- bin/kafka-console-consumer.sh --bootstrap-server my-cluster-kafka-bootstrap:9092 --topic my-topic --from-beginning
```

# Benchmark
```
sudo kubectl -n kafka run kafka-benchmark-producer -ti --image=quay.io/strimzi/kafka:0.40.0-kafka-3.7.0 --rm=true --restart=Never -- bin/kafka-producer-perf-test.sh --topic my-topic --num-records 1000000 --record-size 400 --throughput -1 --producer-props bootstrap.servers=my-cluster-kafka-bootstrap:9092
```

## Results

k3s on i7-3740QM CPU @ 2.70GHz, crappy disk (350MB/s)

| Brokers       | Type | reader/writers |  records/s  |  MB/s |  message size |
|---------------|------|----------------|-------------|-------|---------------|
| 1 | write | 1 | 265k | 101 | 400 |
| 1 | write | 1 | 78k  | 104 | 1400 | 
| 1 | write | 2 | 377k  | 143 | 400 | 
| 1 | write | 4 | 364k  | 138 | 400 |
| 2 | write | 2 | 407k  | 155 | 400 |

Machine is bottleneck - old laptop - load average over 12. 4 cores

Change the replicas to 2 in the kafka yaml file and apply

verify the number of brokers with

```
sudo kubectl -n kafka run kafka-api-versions -ti --image=quay.io/strimzi/kafka:0.40.0-kafka-3.7.0 --rm=true --restart=Never -- bin/kafka-broker-api-versions.sh --bootstrap-server my-cluster-kafka-bootstrap:9092
```

# Install Kafka UI

Install kafka-ui using helm and the repo kafka-ui-values.yaml file

```
helm repo add appscode https://charts.appscode.com/stable/

helm install my-kafka-ui appscode/kafka-ui --version 2024.4.27 --values kafka-ui-values.yaml -n kafka
```

Make sure to install into the same namespace kafka was installed to, otherwise change the DNS namespace accordingly

```
kubectl port-forward svc/my-kafka-ui 8080:80 -n kafka
```

open browser

`http:\\localhost:8080`