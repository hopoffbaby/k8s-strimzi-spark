```
kubectl -n minio-operator run mcadmin -ti --image=minio/warp:latest --rm=true --restart=Never -- --help
```

# T14 laptop with docker desktop (minio server = 4c/8G)

## PUT
```
kubectl -n minio-operator run warp -ti --image=minio/warp:latest --rm=true --restart=Never -- put --insecure --host minio.minio-tenant-source.svc.cluster.local --access-key minio --secret-key password --tls --autoterm --duration 30s --analyze.v
```

Operation: PUT (408). Ran 32s. Size: 10485760 bytes. Concurrency: 20.

Requests considered: 330:
 * Avg: 1.274s, 50%: 417ms, 90%: 4.385s, 99%: 5.202s, Fastest: 279ms, Slowest: 5.223s, StdDev: 1.548s

Throughput:
* Average: 152.59 MiB/s, 15.26 obj/s

Throughput, split into 22 x 1s:
 * Fastest: 535.1MiB/s, 53.51 obj/s (1s, starting 14:33:58 UTC)
 * 50% Median: 59.1MiB/s, 5.91 obj/s (1s, starting 14:34:16 UTC)
 * Slowest: 48.4MiB/s, 4.84 obj/s (1s, starting 14:34:08 UTC)

## GET
```
kubectl -n minio-operator run warp -ti --image=minio/warp:latest --rm=true --restart=Never -- get --insecure --host minio.minio-tenant-source.svc.cluster.local --access-key minio --secret-key password --tls --autoterm --duration 30s --analyze.v
```

----------------------------------------
Operation: PUT (2500). Ran 2m43s. Size: 10485760 bytes. Concurrency: 20.

Requests considered: 2422:
 * Avg: 1.314s, 50%: 415ms, 90%: 4.31s, 99%: 5.291s, Fastest: 112ms, Slowest: 5.726s, StdDev: 1.585s

Throughput:
* Average: 150.59 MiB/s, 15.06 obj/s

Throughput, split into 162 x 1s:
 * Fastest: 616.8MiB/s, 61.68 obj/s (1s, starting 14:39:16 UTC)
 * 50% Median: 61.0MiB/s, 6.10 obj/s (1s, starting 14:37:42 UTC)
 * Slowest: 41.5MiB/s, 4.15 obj/s (1s, starting 14:38:12 UTC)

----------------------------------------
Operation: GET (5428). Ran 30s. Size: 10485760 bytes. Concurrency: 20.

Requests considered: 5334:
 * Avg: 111ms, 50%: 105ms, 90%: 173ms, 99%: 478ms, Fastest: 15ms, Slowest: 1.904s, StdDev: 104ms
 * TTFB: Avg: 33ms, Best: 1ms, 25th: 7ms, Median: 23ms, 75th: 37ms, 90th: 56ms, 99th: 254ms, Worst: 1.601s StdDev: 71ms
 * First Access: Avg: 125ms, 50%: 114ms, 90%: 172ms, 99%: 390ms, Fastest: 22ms, Slowest: 1.27s, StdDev: 79ms
 * First Access TTFB: Avg: 37ms, Best: 2ms, 25th: 20ms, Median: 29ms, 75th: 39ms, 90th: 56ms, 99th: 192ms, Worst: 1.207s StdDev: 52ms
 * Last Access: Avg: 114ms, 50%: 111ms, 90%: 185ms, 99%: 483ms, Fastest: 15ms, Slowest: 1.694s, StdDev: 104ms
 * Last Access TTFB: Avg: 33ms, Best: 1ms, 25th: 5ms, Median: 23ms, 75th: 40ms, 90th: 59ms, 99th: 237ms, Worst: 1.601s StdDev: 73ms

Throughput:
* Average: 1807.31 MiB/s, 180.73 obj/s

Throughput, split into 29 x 1s:
 * Fastest: 2566.7MiB/s, 256.67 obj/s (1s, starting 14:39:59 UTC)
 * 50% Median: 2064.0MiB/s, 206.40 obj/s (1s, starting 14:40:16 UTC)
 * Slowest: 305.8MiB/s, 30.58 obj/s (1s, starting 14:40:13 UTC)

