# Set PowerShell to stop on all errors
$ErrorActionPreference = 'Stop'

#############
# Install operator
#############

helm repo add minio-operator https://operator.min.io

helm repo update

helm install --namespace minio-operator --create-namespace operator minio-operator/operator

kubectl wait deployment/minio-operator --for=condition=Available --timeout=500s -n minio-operator

#operator jwt
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String((kubectl get secret/console-sa-secret -n minio-operator -o json | ConvertFrom-Json).data.token))

#############
# Deploy tenants
#############

kubectl create namespace minio-tenant-source
kubectl apply -f minio-tenant-source.yaml -n minio-tenant-source

kubectl create namespace minio-tenant-dest
kubectl apply -f minio-tenant-dest.yaml -n minio-tenant-dest

kubectl create namespace minio-tenant-mcmirror
kubectl apply -f minio-tenant-mcmirror.yaml -n minio-tenant-mcmirror

#############
# Wait for tenants
#############

# Set the timeout period in seconds
$timeout = 500

# Calculate the end time based on the current time and the timeout period
$end = (Get-Date).AddSeconds($timeout)

Write-Output "Waiting for tenant to be initialized..."

# Loop until the current time is greater than the end time
do {
    # Retrieve the current state of the tenant
    $currentState = kubectl get tenant mcmirror-tenant -n minio-tenant-mcmirror -o jsonpath='{.status.currentState}'

    # Check if the current state is 'Initialized'
    if ($currentState -eq 'Initialized') {
        Write-Output "Tenant is initialized."
        break
    }

    # Output the current state for debugging purposes
    Write-Output "Current state: $currentState"

    # Pause the loop for 5 seconds before checking again
    Start-Sleep -Seconds 5
} while ((Get-Date) -lt $end)

#########
#enable events in source tenant
#########

#kubectl -n minio-operator run mcadmin -ti --image=minio/mc:latest --rm=true --restart=Never -- cp

# set up event notifications on bucket
kubectl exec -it pod/source-tenant-pool-0-0 -n minio-tenant-source -- /bin/sh -c "mc alias set --insecure myminio https://minio minio password && mc event add --insecure myminio/test-bucket1 arn:minio:sqs::PRIMARY:kafka --event put,get,delete,replica,ilm,scanner"

#########
#configure cluster replication

kubectl exec -it pod/source-tenant-pool-0-0 -n minio-tenant-source -- /bin/sh -c "mc alias set --insecure sourceminio https://minio.minio-tenant-source.svc.cluster.local minio password && mc alias set --insecure destminio https://minio.minio-tenant-dest.svc.cluster.local minio password && mc admin replicate add --replicate-ilm-expiry sourceminio destminio"

# as versioning is mandatory for site replication, add a rule ILM rule to delete old versions

#NOT WORKING - apparently mini time is 24h

kubectl exec -it pod/source-tenant-pool-0-0 -n minio-tenant-source -- /bin/sh -c "mc ilm rule add --expire-delete-marker --noncurrent-expire-newer 0 --insecure myminio/test-bucket1"

#can force a delete of non current versions using - BE VERY CAREFUL TO USE THIS COMMAND EXACTLY AS SHOWN - otherwise you can nuke all data
#mc rm --insecure --versions --force --recursive --non-current myminio

#########
#copy files into source tenant
#########
# put some stuff in the bucket to trigger notifications
kubectl exec -it pod/source-tenant-pool-0-0 -n minio-tenant-source -- /bin/sh -c "mc alias set --insecure myminio https://minio minio password && mc cp --insecure --recursive /bin/ myminio/test-bucket1"

#########
#list files and status in dest tenant
kubectl -n minio-tenant-dest run mcadmin -ti --image=minio/mc:latest --rm=true --restart=Never --command -- /bin/sh -c "mc alias set --insecure myminio https://minio minio password && mc ls --insecure myminio/test-bucket1 && mc admin replicate --insecure info myminio && mc admin replicate --insecure status myminio"
#########

#########
# start up mc mirror WAN replication
########

kubectl exec -it pod/source-tenant-pool-0-0 -n minio-tenant-source -- /bin/sh -c "mc alias set --insecure sourceminio https://minio.minio-tenant-source.svc.cluster.local minio password && mc alias set --insecure mirrorminio https://minio.minio-tenant-mcmirror.svc.cluster.local minio password && mc mirror --overwrite --watch --remove --preserve --retry --json --skip-errors --insecure sourceminio/test-bucket1 mirrorminio/test-bucket1"

#Port forwarding
# kubectl port-forward svc/console -n minio-operator 9090:9090
# kubectl port-forward svc/source-tenant-console -n minio-tenant-source 9091:9443
# kubectl port-forward svc/dest-tenant-console -n minio-tenant-dest 9092:9443
# kubectl port-forward svc/mcmirror-tenant-console -n minio-tenant-mcmirror 9093:9443

# Interactive shell into source cluster mc
# kubectl -n minio-tenant-source run mcadmin -ti --image=minio/mc:latest --rm=true --restart=Never --command -- /bin/sh
#or
#kubectl exec -it pod/source-tenant-pool-0-0 -n minio-tenant-source -- /bin/sh

#RESET
# kubectl delete namespace minio-operator minio-tenant-source minio-tenant-dest minio-tenant-mcmirror