#!/bin/bash

# Exit immediately if a command exits with a non-zero status
#set -e

#############
# Install operator
#############

sudo helm repo add minio-operator https://operator.min.io

sudo helm repo update

sudo helm install --kubeconfig /etc/rancher/k3s/k3s.yaml --namespace minio-operator --create-namespace operator minio-operator/operator --version 5.0.15

sudo kubectl wait deployment/minio-operator --for=condition=Available --timeout=500s -n minio-operator

# operator jwt
sudo kubectl get secret/console-sa-secret -n minio-operator -o json | jq -r '.data.token' | base64 --decode

#############
# Deploy tenants
#############

sudo kubectl create namespace minio-tenant-source
sudo kubectl apply -f minio-tenant-source.yaml -n minio-tenant-source

#exit 

sudo kubectl create namespace minio-tenant-dest
sudo kubectl apply -f minio-tenant-dest.yaml -n minio-tenant-dest

sudo kubectl create namespace minio-tenant-mcmirror
sudo kubectl apply -f minio-tenant-mcmirror.yaml -n minio-tenant-mcmirror

#############
# Wait for tenants
#############

# Set the timeout period in seconds
timeout=500

# Calculate the end time based on the current time and the timeout period
end=$((SECONDS+timeout))

echo "Waiting for tenant to be initialized..."

# Loop until the current time is greater than the end time
while [ $SECONDS -lt $end ]; do
    # Retrieve the current state of the tenant
    currentState=$(sudo kubectl get tenant mcmirror-tenant -n minio-tenant-mcmirror -o jsonpath='{.status.currentState}')

    # Check if the current state is 'Initialized'
    if [ "$currentState" == 'Initialized' ]; then
        echo "Tenant is initialized."
        break
    fi

    # Output the current state for debugging purposes
    echo "Current state: $currentState"

    # Pause the loop for 5 seconds before checking again
    sleep 5
done

#########
# enable events in source tenant
#########

# set up event notifications on bucket
sudo kubectl exec -it pod/source-tenant-pool-0-0 -n minio-tenant-source -- /bin/sh -c "mc alias set --insecure myminio https://minio minio password && mc event add --insecure myminio/test-bucket1 arn:minio:sqs::PRIMARY:kafka --event put,get,delete,replica,ilm,scanner"

#########
# configure cluster replication
#########

sudo kubectl exec -it pod/source-tenant-pool-0-0 -n minio-tenant-source -- /bin/sh -c "mc alias set --insecure sourceminio https://minio.minio-tenant-source.svc.cluster.local minio password && mc alias set --insecure destminio https://minio.minio-tenant-dest.svc.cluster.local minio password && mc admin replicate add --replicate-ilm-expiry sourceminio destminio"

# as versioning is mandatory for site replication, add a rule ILM rule to delete old versions

#NOT WORKING

sudo kubectl exec -it pod/source-tenant-pool-0-0 -n minio-tenant-source -- /bin/sh -c "mc alias set --insecure myminio https://minio minio password && mc ilm rule add --expire-delete-marker --noncurrent-expire-newer 1 --noncurrent-expire-days 1 --insecure myminio/test-bucket1"

# I think 0 is not a valid value

#########
# copy files into source tenant
#########

# put some stuff in the bucket to trigger notifications
sudo kubectl exec -it pod/source-tenant-pool-0-0 -n minio-tenant-source -- /bin/sh -c "mc alias set --insecure myminio https://minio minio password && mc cp --insecure --recursive /bin/ myminio/test-bucket1"

#########
# list files and status in dest tenant
#########

sudo kubectl exec -it pod/dest-tenant-pool-0-0 -n minio-tenant-dest -- /bin/sh -c "mc alias set --insecure myminio https://minio minio password && mc ls --insecure myminio/test-bucket1 && mc admin replicate --insecure info myminio && mc admin replicate --insecure status myminio"

#########
# start up mc mirror WAN replication
########

sudo kubectl exec -it pod/source-tenant-pool-0-0 -n minio-tenant-source -- /bin/sh -c "mc alias set --insecure sourceminio https://minio.minio-tenant-source.svc.cluster.local minio password && mc alias set --insecure mirrorminio https://minio.minio-tenant-mcmirror.svc.cluster.local minio password && mc mirror --overwrite --watch --remove --preserve --retry --json --skip-errors --insecure sourceminio/test-bucket1 mirrorminio/test-bucket1"

# Port forwarding
# kubectl port-forward svc/console -n minio-operator 9090:9090
# kubectl port-forward svc/source-tenant-console -n minio-tenant-source 9091:9443
# kubectl port-forward svc/dest-tenant-console -n minio-tenant-dest 9092:9443
# kubectl port-forward svc/mcmirror-tenant-console -n minio-tenant-mcmirror 9093:9443

# Interactive shell into source cluster mc
# kubectl -n minio-tenant-source run mcadmin -ti --image=minio/mc:latest --rm=true --restart=Never -- /bin/sh

# WTF - for some reason with k3s I cant get /bin/sh in the mc container - says command not found. Can use the existing minio container
# sudo kubectl exec -it pod/source-tenant-pool-0-0 -n minio-tenant-source -- /bin/sh

# RESET
# sudo kubectl delete namespace minio-operator minio-tenant-source minio-tenant-dest minio-tenant-mcmirror
