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

# Install Spark Operator


