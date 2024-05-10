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


run the `spark/bootstrapSpark.ps1` script

## Run a job

Submit the spark job from this repo

```
kubectl apply -f .\spark\spark-pi.yaml

kubectl get sparkapplications spark-pi -n test-ns

kubectl describe sparkapplication --namespace=test-ns

...
...
Events:
  Type    Reason                     Age                  From            Message
  ----    ------                     ----                 ----            -------
  Normal  SparkApplicationAdded      2m20s                spark-operator  SparkApplication spark-pi was added, enqueuing it for submission
  Normal  SparkApplicationSubmitted  2m14s                spark-operator  SparkApplication spark-pi was submitted successfully
  Normal  SparkDriverRunning         2m11s                spark-operator  Driver spark-pi-driver is running
  Normal  SparkExecutorPending       2m2s                 spark-operator  Executor [spark-pi-b8d2788f4ebba73c-exec-1] is pending
  Normal  SparkExecutorRunning       117s                 spark-operator  Executor [spark-pi-b8d2788f4ebba73c-exec-1] is running
  Normal  SparkExecutorCompleted     107s                 spark-operator  Executor [spark-pi-b8d2788f4ebba73c-exec-1] completed
  Normal  SparkDriverCompleted       106s                 spark-operator  Driver spark-pi-driver completed
  Normal  SparkApplicationCompleted  106s (x2 over 106s)  spark-operator  SparkApplication spark-pi completed

kubectl describe pod spark-pi-driver -n test-ns

```
## check the spark logs

`kubectl get pods -n test-ns`

can see the driver pod is there in completed state

check its logs

`kubectl logs spark-pi-driver -n test-ns`

kubectl port-forward svc/spark-pi-ui-svc 4040:4040 -n test-ns

http://localhost:4040/

run job and quickly port forward

kubectl delete -f .\spark\spark-pi.yaml
kubectl apply -f .\spark\spark-pi.yaml
kubectl port-forward svc/spark-pi-ui-svc 4040:4040 -n test-ns


