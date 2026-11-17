# Thông tin phần cứng máy test

## Bảng thông số

| Hạng mục | Giá trị |
|---|---|
| Hostname | `zinn-Nitro-AN515-57` |
| OS | `Ubuntu 26.04.1 LTS` |
| Kernel | `Linux zinn-Nitro-AN515-57 7.0.0-43-generic #43-Ubuntu SMP PREEMPT_DYNAMIC Fri Oct 23 13:25:25 UTC 2026 x86_64 GNU/Linux` |
| CPU | `11th Gen Intel(R) Core(TM) i5-11400H @ 2.70GHz`; 1 socket, 6 cores/socket, 2 threads/core; tổng 6 cores / 12 threads |
| RAM | 30 GiB tổng; swap 8.0 GiB |
| Disk | `sda` 931.5G (HGST HTS541010B7E610, ROTA=1); `nvme0n1` 476.9G (WDC PC SN530 SDBPNPZ-512G-1114, ROTA=0); `nvme1n1` 931.5G (CT1000P3PSSD8, ROTA=0) |
| Java | OpenJDK `25.0.5.0.3` |
| Node.js | `v22.22.1` |
| JMeter | `5.6.3` |

## Output nguồn

Các lệnh đã chạy:

```bash
hostname
lscpu
free -h
lsblk -d -o NAME,SIZE,ROTA,MODEL
uname -a
cat /etc/os-release
java -version
node --version
jmeter --version
(screenfetch || neofetch)
```

Kết quả cần xác minh:

```text
$ hostname
zinn-Nitro-AN515-57

$ lscpu
Architecture:                            x86_64
CPU(s):                                  12
Model name:                              11th Gen Intel(R) Core(TM) i5-11400H @ 2.70GHz
Thread(s) per core:                      2
Core(s) per socket:                      6
Socket(s):                               1

$ free -h
               total        used        free      shared  buff/cache   available
Mem:            30Gi        16Gi       3.8Gi       1.9Gi        12Gi        13Gi
Swap:          8.0Gi       1.6Gi       6.4Gi

$ lsblk -d -o NAME,SIZE,ROTA,MODEL
NAME      SIZE ROTA MODEL
sda     931.5G    1 HGST HTS541010B7E610
nvme0n1 476.9G    0 WDC PC SN530 SDBPNPZ-512G-1114
nvme1n1 931.5G    0 CT1000P3PSSD8

$ uname -a
Linux zinn-Nitro-AN515-57 7.0.0-43-generic #43-Ubuntu SMP PREEMPT_DYNAMIC Fri Oct 23 13:25:25 UTC 2026 x86_64 GNU/Linux

$ cat /etc/os-release
PRETTY_NAME="Ubuntu 26.04.1 LTS"
NAME="Ubuntu"
VERSION_ID="26.04"
VERSION="26.04.1 LTS (Resolute Raccoon)"
VERSION_CODENAME=resolute

$ java -version
openjdk version "25.0.5.0.3" 2026-10-24
OpenJDK Runtime Environment (build 25.0.5.0.3+1-1-26.04.1-Ubuntu)
OpenJDK 64-Bit Server VM (build 25.0.5.0.3+1-1-26.04.1-Ubuntu, mixed mode, sharing)

$ node --version
v22.22.1

$ jmeter --version
Apache JMeter 5.6.3

(screenfetch, neofetch: command not found)
```

`lscpu` thực tế báo 1 socket, 6 core mỗi socket, 2 thread mỗi core (12 CPU logic).