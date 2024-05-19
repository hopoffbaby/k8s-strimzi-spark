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

# Cruise control

## deploy cruise control

Strimzi is able to deploy a instance of cruise control (GUI is not supported by default - https://strimzi.io/blog/2023/01/11/hacking-for-cruise-control-ui/).

The most basic configuration involves adding `cruiseControl: {}` to the `kafka` manifest. The strimzi cluster must have at least 2 brokers, otherwise it will not start the cluster (no point having cruise control if there isnt more than 1 broker to balance between)

Additional rules and actions can be configured:

https://strimzi.io/blog/2020/06/15/cruise-control/

## request an optimization proposal

Cruise control will recommend optimizations based on the rules configure. To request a proposal, apply a `KafkaRebalance` resource

`kubectl apply -f kafkaRebalance.yaml -n kafka`

to see the proposal:

`kubectl describe kafkarebalance my-rebalance -n kafka`

Initially this shows a perfect cluster as there is no data. To make it interesting, run the benchmark tool, and then add an additional broker to the cluster, delete the `KafkaRebalance` resource and apply again for force another proposal.

now showing a big partition and leader skew

Remove the `cruiseControl: {}` line from the kafka manifest and apply, then add it again.

wait for brokers to be restarted and cruise control to settle down. New recommendation is then provided

```
kubectl describe kafkarebalance my-rebalance -n kafka
...
...
Status:
  Conditions:
    Last Transition Time:  2024-05-19T19:11:23.784304280Z
    Status:                True
    Type:                  ProposalReady
  Observed Generation:     1
  Optimization Result:
    After Before Load Config Map:  my-rebalance
    Data To Move MB:               0
    Excluded Brokers For Leadership:
    Excluded Brokers For Replica Move:
    Excluded Topics:
    Intra Broker Data To Move MB:         0
    Monitored Partitions Percentage:      100
    Num Intra Broker Replica Movements:   0
    Num Leader Movements:                 0
    Num Replica Movements:                27
    On Demand Balancedness Score After:   83.16903091432891
    On Demand Balancedness Score Before:  78.70730590478658
    Provision Recommendation:             [RackAwareGoal] Remove at least 1 rack with brokers. [ReplicaDistributionGoal] Remove at least 3 brokers.
    Provision Status:                     OVER_PROVISIONED
    Recent Windows:                       1
  Session Id:                             d5a5447e-2e11-4ba7-96e1-ebad2817854b
Events:                                   <none>
```

this then provides some suggestions. in this case will move some replicas, and suggests the size of the cluster is over_provisioned suggest it has more resource assigned than is required.

to trigger the optimization you need to annotate the `KafkaRebalance` resource with `approve`

```
kubectl annotate kafkarebalance my-rebalance strimzi.io/rebalance=approve -n kafka
```

You can then check the progress by describing the resource

```
kubectl describe kafkarebalance my-rebalance -n kafka
```

you can also request that cruise control refresh its proposal

```
kubectl annotate kafkarebalance my-rebalance strimzi.io/rebalance=refresh -n kafka
```

Note: be careful downsizing clusters as they may fail if replicas are assigned to brokers. TBC on process to do this.

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