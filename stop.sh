ps -ef|grep mjpg| awk '{ print $2}' |xargs kill -9
ps -ef|grep controlserver| awk '{ print $2}' |xargs kill -9
