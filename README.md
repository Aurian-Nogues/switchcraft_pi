# DESCRIPTION

This app is for WiFi provisioning over Bluetooth.

# PREREQUISITES

The app uses Network manager to configure the WiFi.

## Install packages

    sudo apt update
    sudo apt install network-manager

## Configure dhcpcd to ignore wlan0

To avoid issues with duplicate instances of wpa_supplicant preventing NetworkManager to work properly, we need to modify the default settings. If we kept the setting as is, the wpa_supplicant will be called twice. The first instance will be called by the wpa_supplicant.service, the second one will be executed by dhcpcd deamon. 

To mitigate this issue, first check `/etc/network/interfaces`; this should be empty except for an include from `/etc/network/interfaces.d` (which is in turn empty). This is valid when we have a fresh install of Raspbian.

Then edit `/etc/dhcpcd.conf`, add line:

    denyinterfaces wlan0

This disables execution of the duplicate wpa_supplicant instance.

Then configure Network Manager to control wlan0 and assume dhcp duties. Edit `/etc/NetworkManager/NetworkManager.conf`:

    [main]
    plugins=ifupdown,keyfile
    dhcp=internal
    
    [ifupdown]
    managed=true

Finaly, restart the raspberry to take the modifications into effect.

`sudo reboot`

Make sure that there is only one wpa_supplicant instance running after reboot

`ps axu | grep supplicant`




# PYTHON part

Python uses Bluez library via bluezero (DBUS)

# PREREQUISITES
Bluez
Python 3.7+

The mandatory Python packages:
```
$ sudo pip3 install dbus-python
$ sudo pip3 install bluezero
```

# EXAMPLE

Direct usage

```console
$ sudo python3.7 main.py
$ sudo python3 main.py
```

Python virtual environment

```
$ sudo apt install libgirepository1.0-dev
$ sudo apt install libcairo2-dev

$ python3.7 -m venv ble-env
$ source ble-env/bin/activate
(ble-env) $ pip3 install dbus-python
(ble-env) $ pip3 install PyGObject
(ble-env) $ pip3 install bluezero
(ble-env) $ pip3 install bisturi
(ble-env) $ pip3 install uptime
(ble-env) $ pip3 install python-networkmanager
(ble-env) $ sudo ble-env/bin/python3.7 main.py
```

# DISPLAY
# chromium drivers recommended by selenium will not work on ARM chips. Use this command to install the right ARM drivers
sudo apt install chromium-chromedriver
$ pip3 install selenium



# setup boot options for kiosk

https://itnext.io/raspberry-pi-read-only-kiosk-mode-the-complete-tutorial-for-2021-58a860474215

install prerequisites using 
sudo apt-get install --no-install-recommends xserver-xorg x11-xserver-utils xinit openbox

edit autostart file using sudo nano /etc/xdg/openbox/autostart, insert those lines:
# Disable any form of screen saver / screen blanking / power management
xset s off
xset s noblank
xset -dpms

## disable starting logs and add boot video
https://florianmuller.com/polish-your-raspberry-pi-clean-boot-splash-screen-video-noconsole-zram

### disable graphical outputs on boot
disable raibow screen :
go to
sudo nano /boot/config.txt
add the last line at very end
disable_splash=1

### change output of pi console
sudo nano /boot/cmdline.txt

In this file you will finde a string of parameters all in line 1. Its important that you add the following exactly at the end of the existing line 1, starting with a space between the exisitng and new. So lets add:

consoleblank=1 logo.nologo quiet loglevel=0 plymouth.enable=0 vt.global_cursor_default=0 plymouth.ignore-serial-consoles splash fastboot noatime nodiratime noram

### boot with video or splash screen
sudo apt-get update
sudo apt-get install omxplayer

Next we tell the pi in the rc.local to play our video on boot:
sudo nano /etc/rc.local

In rc.local add before the end where it says exit 0 these two lines. Don‘t forget to replace my path to the video with yours. You can use all kind of formats, avi, mp4 and more should all work fine as well.

dmesg --console-off
omxplayer /home/pi/myvideo.mp4 &


### finish
sudo reboot
that should be a clean boot


### 
hide mouse
sudo apt install unclutter 
add unclutter -idle 0 & at beginning of bash script


# start scripts before desktop starts
take mainPrgrm.service file
copy to /etc/systemd/system

sudo systemctl enable mainPrgm
sudo systemctl start mainPrgm

for lxsession:

sudo nano sudo nano /etc/xdg/lxsession/LXDE-pi/autostart
add at the end:
@lxterminal -e "/home/pi/frame_pi/execute.sh"

then:
chmod 644 all scripts and files to execute


# make pi read only
sudo dphys-swapfile swapoff
sudo dphys-swapfile uninstall
sudo update-rc.d dphys-swapfile remove

# shut down scripts on boot after autostart

ps -ef | grep python
sudo kill 9 <script number>

