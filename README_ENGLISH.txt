TWICHDRONE
----------
Juan M. Casillas <juanm.casillas@gmail.com>
A proof of concept to integrate various embedded technologies,
in order to "replicate" the Twich drone from Rainbow Six Siege.
11/March/2017

21/March/2017

After three days hard working on video streaming, all of the major problems
related to video distribution has been fixed. The best stream solution was
using MJPEG-STREAMER (fork). Yes, using a <img> element of HTML works
better than <video> streaming. This changes a lot of things, so it's
better start again the documentation process to allow a simple and
clean instalation.

--------------------------------------------------------------------------------
CHAPTER 1. GETTING THE PI UP AND RUNNING.
--------------------------------------------------------------------------------

1.1 Introduction
------------------

First, we need to get the PI Up and running with the following Networks setup:

Client (Phone) <-----WIFI TWICHDRONE01 AP --> [ RASPBERRY ] <-- Gopro WIFI -->

That means: PI wifi adapter doubles as Access Point & Wifi client for
GoPro 3 Wifi AP

Also, we need to config the raspberry system in order to fine tune it. Lets see

We need the following components:

1.2. Raspberry PI 3.
1.3. Raspberry PI CAM 2.1.
1.4. Micro SD (at least 8GB). Get one with WITH data rate (class 10>)
1.5. Gopro 3. (Gopro 4 works different)

1.2. Raspberry PI 3.
--------------------

The Raspberry Pi 3 model B
https://www.raspberrypi.org/products/raspberry-pi-3-model-b/
- Get a GOOD power adapter to power it.

For installation:

- Get USB Mouse
- Get USB Keyboard
- Get and HDMI cable
- Funky network cable / WIFI


1.3. Raspberry PI CAM 2.1.
---------------------------

Differences

version 2.1:    Sony IMX219 8-megapixel sensor
lower versions: OmniVision OV5647

So get the official 2.1 version :-D

The Raspberry Pi Camera Module v2 replaced the original Camera Module in April
2016. The v2 Camera Module has a Sony IMX219 8-megapixel sensor
(compared to the 5-megapixel OmniVision OV5647 sensor of the original camera).

https://www.raspberrypi.org/products/camera-module-v2/

1.4. Micro SD.
---------------

First of all: If you get a slow card, you will pain. Get the best SD you can
 pay. 8 GB it's fine. No need of bigger ones.

Test it (after install Pi, of course)
hdparm -tT /dev/mmcblk0:
/dev/mmcblk0:
 Timing cached reads:   1238 MB in  2.00 seconds = 618.88 MB/sec
 Timing buffered disk reads:  64 MB in  3.04 seconds =  21.04 MB/sec

(by the way, the MicroSD is a lexar 32GB class 10 (4 years old).
With this values, the system works, but ... the faster the better


1.4.1. Toast the Image, Boot the PI
------------------------------------

DISTRO: DEBIAN JESSIE (RASPBIAN)

https://downloads.raspberrypi.org/raspbian_latest
Get the version with GUI (PIXEL), because it's easy to work with it (HDMI,
Keyboard, Etc.) You can go with the  command line, but you need at least one
time the HDMI config (X11)

Download the image (PIXEL) to your PC.

Toast it with DD.

See this:
https://www.raspberrypi.org/documentation/installation/installing-images/mac.md

How to toast

    1) get the disk (df -h)
    /dev/disk6s1   3.7Gi  4.1Mi  3.7Gi   1%   0   0  100%   /Volumes/TWICHDRONE

    2) umount it
    sudo diskutil unmount /dev/disk6s1

    3) uncompress the image

    4) dd it
    sudo dd bs=1m if=2017-03-02-raspbian-jessie.img of=/dev/rdisk6
    (Ctrl-T shows info about progress)

    5) Connect HDMI, USB Keyboard, USB Mouse,
    5) REBOOT, and try to boot RB 3. Wait till prompt,
       Partition will be resized.

DEFAULT USER:   pi (passwd raspberry)
ROOT USER:      root (no password, use sudo su -)


1.4.2. Initial PI Config (Network AP, and so on)
-------------------------------------------------

After booting, we have to configure the network layout. First of all, we need
a WORKING network conection with the internet. Use WIFI, or Cable
(better the latter, due we are going to mess with the WIFI adapter config).

Client (Phone) <-----WIFI TWICHDRONE01 AP ---> [ RASPBERRY ] <-- Gopro WIFI -->

For that, we need to install the following packages:

apt-get install hdparm
apt-get install hostapd dnsmasq
apt-get install cmake libjpeg8-dev

1.4.2.1. Update FIRMWARE (if you didn't)
-----------------------------------------

For getting the latest drivers, and firmware if needed. (Lasts for 10 minutes,
downloading and installing)

# rpi-update see
[https://www.raspberrypi.org/forums/viewtopic.php?f=29&t=167934] for issues

# modprobe bcm2835-v4l2 [to load the cam module, for test.]


1.4.2.1. AP Mode + WIFI Client
------------------------------

We need to configure dnsmasq, network interfaces, and firewall masquerading.
With this config, the same adapter works as AP and wifi client. Very useful.
See config_files directory for the template files.

Network config data:

AP_SSID:            TwichDrone01
AP_IP:              192.168.2.1     [in my WIFI: 192.168.0.163]
AP_PASSWD:          rainbow6
GOPROWIFI_SSID:     GOPROR6
GOPROWIFI_PASSWD:   rainbow6

See https://www.raspberrypi.org/forums/viewtopic.php?t=138730 [anthony19114]
for more info.

Uncomment and edit these lines in /etc/dnsmasq.conf

    interface=lo,uap0
    no-dhcp-interface=lo,wlan0
    dhcp-range=192.168.2.100,192.168.2.200,12h

Edit: /etc/hostapd/hostapd.conf

SSID_OF_AP                          = TwichDrone01
SAME_CHANNEL_NUMBER_AS_WIFI_CLIENT  = 1
WIFI_AP_PASS                        = rainbow6


Add: Change SSID_OF_AP, SAME_CHANNEL_NUMBER_AS_WIFI_CLIENT, WIFI_AP_PASS
[plaintext] SAME_CHANNEL_NUMBER_AS_WIFI_CLIENT MUST be the same channel that
the WIFI AP you will connect, else, it won't work. Check the WIFI channel
using wifi analyzer, or other program that shows the channel.

    interface=uap0
    ssid=[SSID_OF_AP]
    hw_mode=g
    channel=[SAME_CHANNEL_NUMBER_AS_WIFI_CLIENT]
    macaddr_acl=0
    auth_algs=1
    ignore_broadcast_ssid=0
    wpa=2
    wpa_passphrase=[WIFI_AP_PASS]
    wpa_key_mgmt=WPA-PSK
    wpa_pairwise=TKIP
    rsn_pairwise=CCMP

Edit AND add to: /etc/network/interfaces

    auto uap0
    iface uap0 inet static
    address 192.168.2.1
    netmask 255.255.255.0

Edit a new file /usr/local/bin/hostapdstart and add:

    iw dev wlan0 interface add uap0 type __ap
    service dnsmasq restart
    sysctl net.ipv4.ip_forward=1
    iptables -t nat -A POSTROUTING -s 192.168.2.0/24 ! -d 192.168.2.0/24 -j MASQUERADE
    ifup uap0
    hostapd /etc/hostapd/hostapd.conf

Change permissions on /usr/local/bin/hostapdstart

    chmod 667 /usr/local/bin/hostapdstart

Edit and add line to: /etc/rc.local

    hostapdstart >1&

    OR just type hostapdstart if you want to see details or if you do not want
    it to start automatically.

Add to /etc/network/interfaces (remove all other wlan0 anything references).
Change [SSID_OF_NETWORK_TO_CONNECT], [PSK_KEY_OF_NETWORK_TO_CONNECT]:
(you can connect to more WIFI networks, but the CHANNEL number must be the same
add the following block for the required networks)

    auto wlan0
    iface wlan0 inet dhcp
    wpa-ssid [SSID_OF_NETWORK_TO_CONNECT]
    wpa-psk [PSK_KEY_OF_NETWORK_TO_CONNECT]

Replace the psk with yours generated by typing:

    SSID_OF_NETWORK_TO_CONNECT: SSID network to connect (e.g. GOPROWIFI)
    PSK_KEY_OF_NETWORK_TO_CONNECT: wpa_passphrase GOPROWIFI PasswdInPlainText

wpa_passphrase return a structure with three fields. Get the big number:
something like a03133ea3333471b0d33dbd1b2b19233294649968537c35904eb3389a7df65ba

At this point, your raspi should work as AP & WIFI client. Check it with a
Mobile Phone.

1.4.2.2. Check Now GoPro Link (if needed)
------------------------------------------

1) Start the GOPRO with the configured settings, start the WIFI.
2) Start the PI (from boot, to check everything works).
3) After booting you should have:

    # ifconfig -a
    # en0   -> cable        [Adapter IP: if plugged, DHCP asigned]
    # wlan0 -> GoPro Wifi   [Adapter IP: 10.5.5.x]
    # uap0  -> Ap Wifi      [Adapter IP: 192.168.2.1]

4) ping the gopro. Always the same IP: [10.5.5.9]
5) Check it (navigate to http://10.5.5.9:8080)

    NOW, check that you can see live stream
    http://10.5.5.9:8080/live/amba.m3u8  [video stream URL]


See [http://www.goprofanatics.com/forum/gopro-hd-hero3/3541-livestreaming-using-go-pro.html]
 for more info interfacing the GOPRO

Now, were are going to configure the PI for DEVELOPING. Turn off the gopro for
now, change the WLAN to your WIFI AP, or use a cable to connect (better).

LOCAL DEV WIFI:

    SSID:       vodafoneXXXX
    passwd:     ************
    Channel:    9

Edit  /etc/hostapd/hostapd.conf and change ChannelNumber [remember 1 for GOPRO]
Edit /etc/network/interfaces and change wlan0
(wpa_passphrase vodafoneXXXX *********) # put your passphrase here

reboot PI and test.

1.4.2.3. SSHD & SYSTEM CONFIG
--------------------------------

SYSTEM_CONFIG ----------------------------------------------------------------

Speedup IO / Tunning: edit [/etc/sysctrl.conf] and add:

    vm.swappiness=15
    vm.vfs_cache_pressure=50
    vm.dirty_background_ratio=15
    vm.dirty_ratio=20
    vm.min_free_kbytes = 16384

Launch raspi-config script

Do the following commands:

    1) BOOT TO CLI
    2) SET KEYBOARD (ES) optional
    3) AUTOLOGIN TO Pi user (DISABLED)
    4) SET TIME ZONE. [Europe/Madrid, GMT+1]
    6) ENABLE: (disable the rest)
        camera
        ssh
        serial
    7) change name of the host to TwichDrone01
    9) set the wifi country

Now, go to shell

    10) set the password for the pi user
        #sudo su -
        #passwd pi [set rainbow6]

    11) edit /etc/ssh/sshd_config add "UseDNS no"
        # reboot (to apply enable changes)

After reboot, you will log in the CLI.

Change the start delay from NOLIMIT to 15 secs (e.g. when you start without
the GOPRO and it waits forever).

[http://unix.stackexchange.com/questions/186162/how-to-change-timeout-in-systemctl]

edit /lib/systemd/system/networking.service.d/network-pre.conf
(if not found, create it, but in the raspberry it was there)

add: 
    [Service]
    TimeoutStartSec=15

This changed 'no limit' to a limit of 15 seconds, making the system boot much faster if network is disconnected.

AUTOMATE SSH (for rsync) ------------------------------------------------------

In order to develop headless, we're going to configure SSHD.
See [https://pihw.wordpress.com/guides/direct-network-connection/]
for more options.

Now, test you can login from your host server (e.g. ssh -l pi 192.168.0.163)
if everything works, then its turn to enable automate login
(for RSYNC, mainly) [http://www.linuxproblem.org/art_9.html]

1) inside the PI, do:
    #ssh -l pi 192.168.2.1
    log in propertly. (this creates .ssh dir)

2) inside the HOST (development machine)
    #ssh-keygen -t rsa      (emtpy passphrase & pass)
    #cat .ssh/id_rsa.pub    (copy data)

3) back in the pi
    # cd .ssh (/home/pi)
    # vi authorized_keys
    <paste the id_rsa.pub content>

4) inside the HOST
    # ssh -l pi 192.168.0.163 (should no ask password)

NOTES: maybe you need:
    Put the public key in .ssh/authorized_keys2
    Change the permissions of .ssh to 700
    Change the permissions of .ssh/authorized_keys2 to 640


sudo pip install git+https://github.com/dpallot/simple-websocket-server.git

1.5 GOPRO3
----------

GOPRO CONTROL [TBD]: See

    [https://github.com/theContentMint/GoProRemote]
    [https://github.com/KonradIT/goprowifihack]             <-
    [https://github.com/joshvillbrandt/GoProController]
    [https://github.com/joshvillbrandt/goprohero]           <-

We're using goprohero lib [https://github.com/joshvillbrandt/goprohero]. First
of all, 

    pip install goprohero
    this will install also wireless and colorama packages

doc  [http://goprohero.readthedocs.io/en/latest/]
code [https://github.com/joshvillbrandt/goprohero/blob/master/goprohero/GoProHero.py]

Example:

    from goprohero import GoProHero
    camera = GoProHero(password='password')
    camera.command('record', 'on')
    status = camera.status()    


--------------------------------------------------------------------------------
CHAPTER 2. SETUP SOFTWARE AND DEPLOY CODE.
--------------------------------------------------------------------------------

In this chapter we're going to configure the required packages to interface the
ARDUINO (for motor control) and the CAMERA (for stream video).

2.1. CAMERA Streaming
2.2. Python WebSockets
2.3. ARDUINO Interface

2.1. CAMERA Streaming
----------------------

After poking arround with NINGX-RTMP, UVL4, FFMPEG, AVCONV, VLC and GStreamer,
I found that the BEST solution is using MJPEG-Streamer. Why? I need low latency,
and a moderate video quality (and size). Neither of the streaming solutions
works, due:

1) video on adroid requires WebM or MP4 encoding.
2) latency is too HIGH.

I test:
    - nginx with RTMP HLS (H264): works, high latency, don't work on video.js
    on android.
    - UVL4. The WebRTC doesn't work as spected.
      MJPEG stream give me the clue to MJPEG-STREAMER (see below)
      High latency, low quality
    - VLC, FFMPEG, AVCONV: works, but as injectors for NGINX.
      Video.JS can't play H.264 streams into Chrome (android)
      Can't create a WebM stream.
    - GStreamer. "Works" can't use their streams directly.

So I end using MJPEG-STREAMER, a fork of the original MJPEG-STREAMER. This
server sends and stream of JPEGS images, and they are shown inside a <img>
element, instead a <video> one.


2.1.1 INSTALLATION OF MJPEG-STREAMER
------------------------------------

This server is very GOOD because gives customization, low latency and a HTTP
server (only works for the given dir, not support subdirs). Perfect for our
needs.

See [https://github.com/jacksonliam/mjpg-streamer] for info.

    # apt-get install cmake libjpeg8-dev [previously installed in the first step of the document]
    # git clone https://github.com/jacksonliam/mjpg-streamer.git
    # cd mjpg-streamer-experimental
    # make

#export LD_LIBRARY_PATH=.
#./mjpg_streamer -o "output_http.so -w ./www" -i "input_raspicam.so -x 496 -y 279 -fps 25"
#./mjpg_streamer -o "output_http.so -w ./www" -i "input_raspicam.so -x 768 -y 432 -fps 25"

In more avanced config (see later) www points to OUR www directory (with the files for the
interface). This works perfectly.

List of "perfect" resolutions see [https://antifreezedesign.wordpress.com/2011/05/13/permutations-of-1920x1080-for-perfect-scaling-at-1-77/]

896 x 504
880 x 495
864 x 486
848 x 477
832 x 468
816 x 459
800 x 450
784 x 441
768 x 432 <-- current one. A good balance in size, quality and bandwitdh
752 x 423
736 x 414
720 x 405
704 x 396
688 x 387
672 x 378
656 x 369
640 x 360
624 x 351
608 x 342
592 x 333
576 x 324
560 x 315

2.2. Python WebSockets
----------------------

In order to work, we need Python WebSocket Server implementation. I ended using
simple-websocket-server a fast, light and easy implementation that works in
python 2.7 (see [https://github.com/dpallot/simple-websocket-server])

WebSockets are used to interconnect the User interface with the control
server (see ARCHITECTURE). Installation is really easy:

    #pip install git+https://github.com/dpallot/simple-websocket-server.git

    The thing is ready to work

2.3. ARDUINO Interface
-----------------------

We are going to use:

     ARDUINO UNO [CLONE] [https://www.amazon.es/gp/product/B01C2Q0NNS/ref=oh_aui_detailpage_o04_s00?ie=UTF8&psc=1]
     ARDUINO MOTOR SHIELD [https://www.arduino.cc/en/Main/ArduinoMotorShieldR3]

    Function    pins per Ch. A   pins per Ch. B
    DIRECTION              D12              D13
    PWM                     D3              D11
    BRAKE                   D9               D8 
    Current Sensing         A0               A1 *not used

    [https://www.allaboutcircuits.com/projects/arduino-motor-shield-tutorial/]
    
    HOW TO WORK:
    1) First you need to set the motor direction (polarity of the power supply) 
      by setting it either HIGH or LOW.
        DIRECTION=0|1
    2) Then you need to disengage the brake pin for the motor channel by 
      setting it to LOW.
        BRAKE=0
    3) Finally, to get the motor to start moving, you need to set the speed by 
        sending a PWM command (analogWrite) to the appropriate pin.
        PWM=0-255
        
    void setup() {

        // A        
        pinMode(12,OUTPUT);      //Channel A Direction Pin Initialize
        pinMode(8,OUTPUT);       //Channel A Brake Pin Initialize

        // B
        pinMode(13,OUTPUT);      //Channel B Direction Pin Initialize
        pinMode(9,OUTPUT);       //Channel B Brake Pin Initialize 
        
        
    }

    function GetCurrent(char motor) {

        int currentpin = (motor == 'B' ? A1 : A0 );    
        float volt_per_amp = 1.65;
    
        float currentRaw   = analogRead(currentPin);
        float currentVolts = currentRaw *(5.0/1024.0);
        float currentAmps = currentVolts/volt_per_amp;
    
        return(currentAmps);
    
    }

    void loop(){
        
        //forward @ full speed
        digitalWrite(12, HIGH);  //Establishes forward direction of Channel A
        digitalWrite(9, LOW);    //Disengage the Brake for Channel A
        analogWrite(3, 255);     //Spins the motor on Channel A at full speed
  
        delay(3000);             //3 seconds
        digitalWrite(9, HIGH);   //Eengage the Brake for Channel A
        delay(3000);
  
        //backward @ half speed
        digitalWrite(12, LOW);   //Establishes backward direction of Channel A
        digitalWrite(9, LOW);    //Disengage the Brake for Channel A
        analogWrite(3, 123);     //Spins the motor on Channel A at half speed
  
  
        Serial.println(GetCurrent('A'));
        Serial.println(GetCurrent('B'));
  
    }

2.3.1 ARDUINO CH340 USB/Serial Driver (For Clones)
--------------------------------------------------

[In my case, Ch341 is detected properly]

FIRST of all: If you have an ARDUINO with USB controller CH340/341g (Chinese
clones) you should see [https://github.com/aperepel/raspberrypi-ch340-driver]
the CH340 driver for raspberry.

    #wget https://github.com/aperepel/raspberrypi-ch340-driver/releases/download/4.4.11-v7/ch34x.ko
    #sudo insmod ch34x.ko
    #lsmod |grep usbserial (should show something like ch341)
    #ls /lib/modules/$(uname -r)/kernel/drivers/usb/serial (it's installed)
    #if not installed  depmod -a

    Plug the Arduino and check for 340/341 strings lsub.
    #lsusb|grep 34.

MAC, install this:
[https://tzapu.com/making-ch340-ch341-serial-adapters-work-under-el-capitan-os-x/]
[https://blog.sengotta.net/signed-mac-os-driver-for-winchiphead-ch340-serial-bridge/]

2.3.2 INSTALL NANPY
--------------------

NANPY allows Raspberry to program directly the ARDUINO BOARD using the Serial
Port, from Python. It have two componentes, NANPY-FIRWMARE (that runs in the
Arduino), and the MASTER controller (HOST) that runs python scripts. You need
the two things installed.

2.3.2.1 - RASPBERRY PI (MASTER controller) INSTALL ----------------------------

Easy. Just: [https://pypi.python.org/pypi/nanpy]

    #pip install pyserial
    #pip install nanpy
    (they come previously installed in the Raspbian jessie)
    
Ready to send commands to the ARDUINO.
see [see https://www.raspberrypi.org/forums/viewtopic.php?t=46881]

Due we are using a CH340, the PORT is other: Just. Read it from ARDUINO IDE,
and initialize the serial Manager:

SerialManager(device='/dev/cu.wchusbserial1a1130')


#example

from nanpy import (ArduinoApi, SerialManager)
from time import sleep

#connection = SerialManager()
connection = SerialManager(device='/dev/cu.wchusbserial1a1130')

a = ArduinoApi(connection=connection)

a.pinMode(13, a.OUTPUT)

for i in range(10000):
    a.digitalWrite(13, (i + 1) % 2)
    sleep(0.2)
    

2.3.2.2 - ARDUINO (Client FIRMWARE) INSTALL -----------------------------------

From your development host (easier):

    #git clone https://github.com/nanpy/nanpy-firmware.git
    #cd nanpy-firmware
    #./configure.sh

    edit Nanpy/cfg.h for configuration (serial, baud rate...)

    Copy Nanpy directory under your "sketchbook" directory, start your
    Arduino IDE, open Sketchbook/Nanpy, select "Upload".

    see [http://www.akeric.com/blog/?p=2420]

--------------------------------------------------------------------------------
CHAPTER 3. INTEGRATING EVERYTHING TOGETHER 
--------------------------------------------------------------------------------

See the blog entry for more details & diagrams.
http://blog.capitanpenurias.com/2017/04/raspberry-pi-arduino-twichdrone.html

