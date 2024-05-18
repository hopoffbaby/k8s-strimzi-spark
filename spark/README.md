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


## Queuing

# basic namespace quota enforcement

Basic namespace quota enforcement will just fail jobs if there is not enough resource to start them

when installing the spark-operator, set `enableResourceQuotaEnforcement=true`. This will make spark operator aware of quota restrictions on the namespace. 

Combine this with `webhook-fail-on-error=true` means that if the job cant run, it will be put into a terminal state of `FAILED`

`kubectl describe quota --all-namespaces`

`kubectl get sparkapplication --namespace=test-ns`

# Advanced scheduling with volcano