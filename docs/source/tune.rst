root@axilleas:~# egrep '  server\b' /etc/haproxy/haproxy.cfg|wc
   2016    6124   67029
root@axilleas:~# grep ^backend /etc/haproxy/haproxy.cfg|wc
    205     410    3805
root@axilleas:~# grep ^frontend /etc/haproxy/haproxy.cfg|wc
    205     410    4215
root@axilleas:~# grep ^frontend /etc/haproxy/haproxy.cfg|wc
    205     410    4215
root@axilleas:~# grep ^backend /etc/haproxy/haproxy.cfg|wc
    205     410    3805
root@axilleas:~# egrep '  server\b' /etc/haproxy/haproxy.cfg|wc
  20016   60124  679029
root@axilleas:~#


pparissis at axilleas in ~
for n in 1 2 3 4 5 6; do /usr/bin/time -f %e haproxytool -D /run/haproxy frontend -r frontend2_proc34;done
frontend2_proc34 0
2.29
frontend2_proc34 0
2.31
frontend2_proc34 0
2.35
frontend2_proc34 0
2.32
frontend2_proc34 0
2.34
frontend2_proc34 0
2.32
pparissis at axilleas in ~
for n in 1 2 3 4 5 6; do /usr/bin/time -f %e haproxytool -D /run/haproxy frontend -r frontend2_proc34;done
frontend2_proc34 0
1.19
frontend2_proc34 0
1.22
frontend2_proc34 0
1.16
frontend2_proc34 0
1.23
frontend2_proc34 0
1.23
frontend2_proc34 0
1.17
pparissis at axilleas in ~



pparissis at axilleas in ~/repo/github/haproxyadmin on (socket-cmd-optimization
$ u+3)
grep '  server ' /etc/haproxy/haproxy.cfg|wc -l
10016
pparissis at axilleas in ~/repo/github/haproxyadmin on (socket-cmd-optimization
$ u+3)
grep '^backend' /etc/haproxy/haproxy.cfg|wc -l
105
pparissis at axilleas in ~/repo/github/haproxyadmin on (socket-cmd-optimization
$ u+3)
grep '^frontend' /etc/haproxy/haproxy.cfg|wc -l
105
pparissis at axilleas in ~/repo/github/haproxyadmin on (socket-cmd-optimization
$ u+3)


for run in 1 2 3 4 5; do echo -n "#${run}: "; /usr/bin/time -f '%e' haproxytool
-D /run/haproxy frontend -r >/dev/null;done
#1: 71.36
#2: 73.16
#3: 71.69
#4: 71.45
#5: 71.15
pparissis at axilleas in ~
for run in 1 2 3 4 5; do echo -n "#${run}: "; /usr/bin/time -f '%e' haproxytool
-D /run/haproxy frontend -r >/dev/null;done
#1: 0.63
#2: 0.62
#3: 0.64
#4: 0.78
#5: 0.60
pparissis at axilleas in ~

WLC in seconds 5 runs
      old  new code
#1: 71.36 0.63
#2: 73.16 0.62
#3: 71.69 0.64
#4: 71.45 0.78
#5: 71.15 0.60
Avg:   72 0.65
