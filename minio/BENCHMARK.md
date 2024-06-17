```
kubectl -n minio-operator run mcadmin -ti --image=minio/warp:latest --rm=true --restart=Never -- --help
```

# T14 laptop with docker desktop

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

# d-arc-itd-clt01 k3s 

## PUT
----------------------------------------
Operation: PUT (2420). Ran 30s. Size: 10485760 bytes. Concurrency: 20.

Requests considered: 2329:
 * Avg: 249ms, 50%: 250ms, 90%: 291ms, 99%: 350ms, Fastest: 69ms, Slowest: 388ms, StdDev: 40ms

Throughput:
* Average: 802.02 MiB/s, 80.20 obj/s

Throughput, split into 29 x 1s:
 * Fastest: 905.3MiB/s, 90.53 obj/s (1s, starting 15:03:32 UTC)
 * 50% Median: 810.9MiB/s, 81.09 obj/s (1s, starting 15:03:17 UTC)
 * Slowest: 693.5MiB/s, 69.35 obj/s (1s, starting 15:03:12 UTC)

## GET

Requests considered: 2417:
 * Avg: 230ms, 50%: 228ms, 90%: 270ms, 99%: 337ms, Fastest: 59ms, Slowest: 505ms, StdDev: 37ms

Throughput:
* Average: 869.15 MiB/s, 86.92 obj/s

Throughput, split into 28 x 1s:
 * Fastest: 970.1MiB/s, 97.01 obj/s (1s, starting 15:05:05 UTC)
 * 50% Median: 882.9MiB/s, 88.29 obj/s (1s, starting 15:04:40 UTC)
 * Slowest: 669.9MiB/s, 66.99 obj/s (1s, starting 15:04:55 UTC)

----------------------------------------
Operation: GET (4842). Ran 30s. Size: 10485760 bytes. Concurrency: 20.

Requests considered: 4718:
 * Avg: 123ms, 50%: 25ms, 90%: 357ms, 99%: 749ms, Fastest: 14ms, Slowest: 1.109s, StdDev: 169ms
 * TTFB: Avg: 27ms, Best: 1ms, 25th: 2ms, Median: 3ms, 75th: 45ms, 90th: 87ms, 99th: 177ms, Worst: 359ms StdDev: 42ms
 * First Access: Avg: 144ms, 50%: 118ms, 90%: 334ms, 99%: 566ms, Fastest: 14ms, Slowest: 980ms, StdDev: 140ms
 * First Access TTFB: Avg: 39ms, Best: 1ms, 25th: 2ms, Median: 26ms, 75th: 62ms, 90th: 100ms, 99th: 192ms, Worst: 348ms StdDev: 46ms
 * Last Access: Avg: 158ms, 50%: 23ms, 90%: 468ms, 99%: 830ms, Fastest: 14ms, Slowest: 1.109s, StdDev: 209ms
 * Last Access TTFB: Avg: 33ms, Best: 1ms, 25th: 2ms, Median: 2ms, 75th: 59ms, 90th: 102ms, 99th: 201ms, Worst: 359ms StdDev: 49ms

Throughput:
* Average: 1619.75 MiB/s, 161.98 obj/s

Throughput, split into 29 x 1s:
 * Fastest: 3525.5MiB/s, 352.55 obj/s (1s, starting 15:05:11 UTC)
 * 50% Median: 1588.9MiB/s, 158.89 obj/s (1s, starting 15:05:18 UTC)
 * Slowest: 384.8MiB/s, 38.48 obj/s (1s, starting 15:05:36 UTC)


# d-arc-itd-clt01 k3s single node single disk (limits 2CPU, 4Gi)

## GET - maxed 2000mCPU 3Gi
```
sudo kubectl -n minio-operator run warp -ti --image=minio/warp:latest --rm=true --restart=Never -- get --insecure --host minio.minio-tenant-source.svc.cluster.local --access-key minio --secret-key password --tls --autoterm --duration 30s --analyze.v
```

Operation: PUT (2500). Ran 1m6s. Size: 10485760 bytes. Concurrency: 20.

Requests considered: 2409:
 * Avg: 532ms, 50%: 561ms, 90%: 660ms, 99%: 792ms, Fastest: 75ms, Slowest: 909ms, StdDev: 128ms

Throughput:
* Average: 375.48 MiB/s, 37.55 obj/s

Throughput, split into 64 x 1s:
 * Fastest: 413.4MiB/s, 41.34 obj/s (1s, starting 15:25:47 UTC)
 * 50% Median: 378.5MiB/s, 37.85 obj/s (1s, starting 15:25:44 UTC)
 * Slowest: 302.8MiB/s, 30.28 obj/s (1s, starting 15:25:09 UTC)

----------------------------------------
Operation: GET (1739). Ran 30s. Size: 10485760 bytes. Concurrency: 20.

Requests considered: 1657:
 * Avg: 347ms, 50%: 355ms, 90%: 439ms, 99%: 526ms, Fastest: 18ms, Slowest: 645ms, StdDev: 92ms
 * TTFB: Avg: 92ms, Best: 2ms, 25th: 73ms, Median: 93ms, 75th: 111ms, 90th: 137ms, 99th: 188ms, Worst: 251ms StdDev: 38ms
 * First Access: Avg: 361ms, 50%: 364ms, 90%: 442ms, 99%: 517ms, Fastest: 17ms, Slowest: 625ms, StdDev: 69ms
 * First Access TTFB: Avg: 96ms, Best: 3ms, 25th: 76ms, Median: 95ms, 75th: 113ms, 90th: 140ms, 99th: 190ms, Worst: 251ms StdDev: 35ms
 * Last Access: Avg: 345ms, 50%: 350ms, 90%: 434ms, 99%: 515ms, Fastest: 18ms, Slowest: 645ms, StdDev: 90ms
 * Last Access TTFB: Avg: 91ms, Best: 2ms, 25th: 72ms, Median: 93ms, 75th: 110ms, 90th: 134ms, 99th: 188ms, Worst: 251ms StdDev: 38ms

Throughput:
* Average: 575.43 MiB/s, 57.54 obj/s

Throughput, split into 29 x 1s:
 * Fastest: 615.4MiB/s, 61.54 obj/s (1s, starting 15:26:32 UTC)
 * 50% Median: 578.4MiB/s, 57.84 obj/s (1s, starting 15:26:25 UTC)
 * Slowest: 524.1MiB/s, 52.41 obj/s (1s, starting 15:26:11 UTC)
