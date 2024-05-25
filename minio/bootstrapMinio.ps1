# Set PowerShell to stop on all errors
$ErrorActionPreference = 'Stop'

helm repo add minio-operator https://operator.min.io

helm install --namespace minio-operator --create-namespace operator minio-operator/operator

kubectl wait deployment/minio-operator --for=condition=Available --timeout=500s -n minio-operator

#operator jwt
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String((kubectl get secret/console-sa-secret -n minio-operator -o json | ConvertFrom-Json).data.token))

kubectl apply -f minio-tenant.yaml -n minio-operator

# Set the timeout period in seconds
$timeout = 500

# Calculate the end time based on the current time and the timeout period
$end = (Get-Date).AddSeconds($timeout)

Write-Output "Waiting for tenant to be initialized..."

# Loop until the current time is greater than the end time
do {
    # Retrieve the current state of the tenant
    $currentState = kubectl get tenant tenant-name -n minio-operator -o jsonpath='{.status.currentState}'

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

#kubectl -n minio-operator run mcadmin -ti --image=minio/mc:latest --rm=true --restart=Never -- cp

# set up event notifications on bucket
kubectl -n minio-operator run mcadmin -ti --image=minio/mc:latest --rm=true --restart=Never --command -- /bin/sh -c "mc alias set --insecure myminio https://minio minio password && mc event add --insecure myminio/test-bucket1 arn:minio:sqs::PRIMARY:kafka --event put,get,delete,replica,ilm,scanner"

# put some stuff in the bucket to trigger notifications
kubectl -n minio-operator run mcadmin -ti --image=minio/mc:latest --rm=true --restart=Never --command -- /bin/sh -c "mc alias set --insecure myminio https://minio minio password && mc cp --insecure --recursive /bin/ myminio/test-bucket1"