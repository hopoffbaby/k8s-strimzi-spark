A collection of examples for `Strimzi`/`Kafka`, `Spark`, and `Volcano`

# Goals

## Kafka 
- [x] Install Strimzi
- [x] Deploy cluster
- [x] Produce / consume messages
- [x] Adjust number of brokers
- [x] Benchmark perfomace
- [x] Deploy Kafka UI


- [ ] Topic compression
- [ ] Backup / restore
- [ ] OIDC
- [ ] Rack awareness

- [ ] Monitoring
- [x] Cruise Control
- [ ] Quotas
- [ ] Retention policies
- [ ] Scale up/down

- [x] Mirror maker
- [ ] autoscaling brokers
- [ ] Karapace deployment
- [ ] Karapace security

## Minio

- [x] single node single disk deploy to k8s
- [x] bucket notifications into kafka

## VAP emulator

- [ ] Object input
- [ ] Object output
- [ ] Auto scaling
- [ ] ffmpeg process
- [ ] Get args from kafka

## S3 <--> POSIX

[Smart guy](http://gaul.org/talks/s3fs-tradeoffs/)

[Smart guys video](https://www.youtube.com/watch?v=zqksYmExju4)

S3 == eventual consistency

### S3Proxy
[S3Proxy](https://github.com/gaul/s3proxy) - access a file system using the S3 API

### Native Object Access

#### S3FS
[s3fs](https://github.com/s3fs-fuse/s3fs-fuse)


#### Goofys
[Goofys](https://github.com/kahing/goofys)

Faster but less POSIX-y

#### rclone
[rclone](https://github.com/rclone)

like rsync for cloud, but offers a fuse mount option

#### Weka S3 
based on MinIO - allows s3 access to SMB/NFS/WekaFS data

#### CunoFS
Paid solution

### Block S3 access

#### s3ql

treats object store like block device. Lacks native object access. 

#### JuiceFS
treats like block storage. 



