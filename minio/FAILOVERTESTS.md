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

## 6 nodes, 6 drives, EC:3 (K3 M3)

## full health

### live
GET https://localhost:9000/minio/health/live 200

### read quorum
GET https://localhost:9000/minio/health/cluster/read 200

### write quorum
GET https://localhost:9000/minio/health/cluster 200

### maintenance check
GET https://localhost:9000/minio/health/cluster?maintenance=true 200

## 2 pods killed with chaos mesh (4&5)

### live
GET https://localhost:9000/minio/health/live 200

### read quorum
GET https://localhost:9000/minio/health/cluster/read 200

### write quorum
GET https://localhost:9000/minio/health/cluster 200

### maintenance check
GET https://localhost:9000/minio/health/cluster?maintenance=true 412

412 means cluster will not have write quorum if another node is taken offline. This is expected, 3 drives remaining online is == than K=3. because K = 1/2N quorum needs to be K+1 = 4 for write quorum


## 3 pods (50%) killed with chaos mesh (3 & 4 & 5)

### live
GET https://localhost:9000/minio/health/live 200

### read quorum
GET https://localhost:9000/minio/health/cluster/read 200

### write quorum
GET https://localhost:9000/minio/health/cluster 503

write quorum is lost - expected

### maintenance check
GET https://localhost:9000/minio/health/cluster?maintenance=true 412

412 means cluster will not have write quorum if another node is taken offline. write quorum is already lost. This is expected, 2 drives remaining online is == than K=3. because K = 1/2N quorum needs to be K+1 = 4 for write quorum

### notes
Unable to log onto to GUI

Using `S3 browser` to upload a file 

"Failed - SlowDownWrite: Resource requested is unwritable, please reduce your request rate" - as expected

Can sucessfully download a file - as expected

# Site replication

set up 2 sites in sync rep. 

Copied files to site 1, replicated across.

Kill site 2 using chaos mesh

Upload new file to site 1

pause chaos mesh experiment to bring site 2 back to life

file available in site 2

deleted files in site 1, very quickly reflected in site 2

# slow site repliaction proxying 