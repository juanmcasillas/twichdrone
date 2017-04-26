#!/bin/sh

HPI=/home/pi
SDIR=$HPI/mjpg-streamer/mjpg-streamer-experimental

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$SDIR

#$SDIR/mjpg_streamer -o "output_http.so -w $HPI/TwichDrone/www -p 80" -i "input_raspicam.so -x 768 -y 432 -fps 25 -vf -hf" -o "output_file.so -f $HPI/TwichDrone/stream -m stream.mjpeg" &

$SDIR/mjpg_streamer -o "output_http.so -w $HPI/TwichDrone/www -p 80" -i "input_raspicam.so -x 768 -y 432 -fps 25 -vf -hf" &

cd $HPI/TwichDrone/python; python $HPI/TwichDrone/python/controlserver.py -a 192.168.2.1 -p 8000 -g rainbow6 -f 60 &
