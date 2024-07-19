# 4 nodes 2 drives each - EC:3 (K5 M3)

## full health

kubectl port-forward svc/minio -n minio-tenant-source 5000:443

POSTMAN 

### live
GET https://localhost:5000/minio/health/live 200

### read quorum
GET https://localhost:5000/minio/health/cluster/read 200

### write quorum
GET https://localhost:5000/minio/health/cluster 200

### maintenance check
GET https://minio.example.net:5000/minio/health/cluster?maintenance=true 200

## Kill one pod using chaos mesh

1 server offline, 2 drives offline

GUI flapping, kubectl port-forward keeps failing

delete minio operator namespace

switch to killing source-tenant-pool-0-3

1 server offline, 2 drives offline

seems happier

### live
GET https://localhost:5000/minio/health/live 200

### read quorum
GET https://localhost:5000/minio/health/cluster/read 200

### write quorum
GET https://localhost:5000/minio/health/cluster 200

### maintenance check
GET https://minio.example.net:5000/minio/health/cluster?maintenance=true 412

412 means cluster will not write quorum if another node is taken offline. This is expected, 4 drives offline is greater than K=5  therefore quorum is lost

## Kill one pod with chaos mesh, and remove 1 drive 
kubectl exec -it pod/source-tenant-pool-0-2 -n minio-tenant-source -- /bin/sh

mv /export1 /export2

Still shows 6/8 drives healthy

kubectl delete pv pvc-ec51bdf0-d858-4d25-a2b1-d1f932474e87 --force=true

still shows healthy drives

deleted pod pod/source-tenant-pool-0-3

This caused one offline pod and 3 offline drives :)

quickly back to health tho






