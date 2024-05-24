# Set PowerShell to stop on all errors
$ErrorActionPreference = 'Stop'

# Create the Kafka namespace
kubectl create namespace kafka

# Install Strimzi in the Kafka namespace
kubectl create -f 'https://strimzi.io/install/latest?namespace=kafka' -n kafka

# Add the Appscode Helm repository
helm repo add appscode https://charts.appscode.com/stable/

# Install the Kafka UI using Helm
helm install kafka-ui-local appscode/kafka-ui --version 2024.4.27 --values kafka-ui-values-local.yaml -n kafka

helm install kafka-ui-remote appscode/kafka-ui --version 2024.4.27 --values kafka-ui-values-remote.yaml -n kafka

# Deploy the Kafka clusters
kubectl apply -f kafka-local.yaml -n kafka
kubectl apply -f kafka-remote.yaml -n kafka

# Wait for the Kafka cluster to be ready
kubectl wait kafka/my-cluster-local --for=condition=Ready --timeout=300s -n kafka 
kubectl wait kafka/my-cluster-remote --for=condition=Ready --timeout=300s -n kafka 

# Deploy mirror maker
kubectl apply -f mirrormaker.yaml -n kafka
kubectl wait kafkamirrormaker2/my-mirror-maker2 --for=condition=Ready --timeout=300s -n kafka 

# Run a Kafka benchmark producer to test the cluster
kubectl -n kafka run kafka-benchmark-producer -ti --image=quay.io/strimzi/kafka:0.40.0-kafka-3.7.0 --rm=true --restart=Never -- bin/kafka-producer-perf-test.sh --topic my-topic --num-records 1000000 --record-size 1000 --throughput -1 --producer-props bootstrap.servers=my-cluster-local-kafka-bootstrap:9092 compression.type=none batch.size=32000 linger.ms=20 partitioner.class=org.apache.kafka.clients.producer.RoundRobinPartitioner acks=all

# consume some messages
kubectl -n kafka run consumer -ti --image=quay.io/strimzi/kafka:0.40.0-kafka-3.7.0 --rm=true --restart=Never -- bin/kafka-consumer-perf-test.sh --topic my-topic --messages 1000000 --bootstrap-server=bootstrap.servers=my-cluster-local-kafka-bootstrap:9092

# Apply the Kafka rebalance configuration
# kubectl apply -f kafkaRebalance.yaml -n kafka

