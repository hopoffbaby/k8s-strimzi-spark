# Set PowerShell to stop on all errors
$ErrorActionPreference = 'Stop'

# Create the Kafka namespace
kubectl create namespace kafka

# Install Strimzi in the Kafka namespace
kubectl create -f 'https://strimzi.io/install/latest?namespace=kafka' -n kafka

# Add the Appscode Helm repository
helm repo add appscode https://charts.appscode.com/stable/

# Install the Kafka UI using Helm
helm install my-kafka-ui appscode/kafka-ui --version 2024.4.27 --values kafka-ui-values.yaml -n kafka

# Apply the Kafka persistent single cluster configuration
kubectl apply -f kafka-persistent-single.yaml -n kafka

# Wait for the Kafka cluster to be ready
kubectl wait kafka/my-cluster --for=condition=Ready --timeout=300s -n kafka 

# Run a Kafka benchmark producer to test the cluster
kubectl -n kafka run kafka-benchmark-producer -ti --image=quay.io/strimzi/kafka:0.40.0-kafka-3.7.0 --rm=true --restart=Never -- bin/kafka-producer-perf-test.sh --topic my-topic --num-records 1000000 --record-size 400 --throughput -1 --producer-props bootstrap.servers=my-cluster-kafka-bootstrap:9092 compression.type=none batch.size=40000 linger.ms=1 partitioner.class=org.apache.kafka.clients.producer.RoundRobinPartitioner acks=1

# consume some messages
kubectl -n kafka run kafka-benchmark-producer -ti --image=quay.io/strimzi/kafka:0.40.0-kafka-3.7.0 --rm=true --restart=Never -- bin/kafka-consumer-perf-test.sh --topic my-topic --messages 100000 --bootstrap-server=bootstrap.servers=my-cluster-kafka-bootstrap:9092

# Apply the Kafka rebalance configuration
kubectl apply -f kafkaRebalance.yaml -n kafka

