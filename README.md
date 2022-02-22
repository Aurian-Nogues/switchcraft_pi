# DESCRIPTION

These instructions are to be used to build SwitchCraft on a Raspberry Pi.
More information at http://switchcraft-nft.io/landing
Additional tutorials to build a button for SwitchCraft using a Nano board can be found at https://github.com/Aurian-Nogues/switchcraft_nano

## Install a fresh Raspberry Pi OS to a micro SD card
* Go to https://www.raspberrypi.com/software/ to downlaod Raspberry Pi Imager
* Choose Raspberry Pi OS and install it on the SD card
* When finished, install the card in your Pi and boot it
* Plug an HDMI monitor, keyboard and mouse to the Pi to start setup

## Setup your Raspberry Pi
* Follow all instructions to make initial Pi setup (update, wifi setting, etc)

## Install all required Linux packages
* Open a terminal (CTRL + ALT + T)
* Type the following commands:
```
sudo apt install network-manager
sudo apt install libgirepository1.0-dev
sudo apt install libcairo2-dev
sudo apt-get install unclutter
```
We use Selenium to display the NFTs through Chromium.
However, Chromium drivers recommended by Selenium do not work with the Pi ARM chips.
Use this command to install the right ARM drivers for Chromium
```
sudo apt install chromium-chromedriver
```

## Setup network parameters
We need to change network settings so Linux network can be controlled by our Python scripts (and indirectly bluetooth).
This will prevent you from "manually" changing network settings.

### prevent normal network manager
Here we configure dhcpcd to ignore wlan0
To avoid issues with duplicate instances of wpa_supplicant preventing NetworkManager to work properly, we need to modify the default settings. If we kept the setting as is, the wpa_supplicant will be called twice. The first instance will be called by the wpa_supplicant.service, the second one will be executed by dhcpcd deamon. 

Type this command to open the text editor:
```
sudo nano /etc/dhcpcd.conf
```
Add the following line at the end of the file:
```
denyinterfaces wlan0
```
press CTRL + X -> Y to save and close

### confiugure network manager to control wlan0
Type this command to open the text editor:
```
sudo nano /etc/NetworkManager/NetworkManager.conf
```
Replace the file content with these lines:
```
[main]
plugins=ifupdown,keyfile
dhcp=internal
    
[ifupdown]
managed=true
```
press CTRL + X -> Y to save and close

Restart the Pi for modifications to take effect
```
sudo reboot
```
Type this if you want to see all available supplicants (this step is not needed to setup SwitchCraft) 
```
ps axu | grep supplicant
```

## Setup SwitchCraft packages
### Copy repo
Open a new terminal and copy the code repository:
```
git clone https://github.com/Aurian-Nogues/switchcraft_pi.git
```

### setup Python environment
Navigate to the repo
```
cd switchcraft_pi
```
Create a Python virtual environment. This will enable us to install all the packages we need isolated from the rest of our OS so we have a clean environment
```
python3 -m venv venv
```
Activate the environment
```
source venv/bin/activate
```
Install all necessary packages
```
pip3 install -r requirements.txt
```

### get scripts to automatically start when the Pi starts

#### start scripts before desktop starts
##### main Python script (Bluetooth receiver, Wifi controller, interactions with SwitchCraft app)
take mainPrgrm.service file from switchcraft_pi and 
copy to /etc/systemd/system using this command:

```
sudo cp ~/switchcraft_pi/mainPrgm.service  /etc/systemd/system
```
Navigate to the folder and check that mainPrgrm.services is there (along with a lot of other files that were already there from OS install)
```
cd /etc/systemd/system
ls
```
We now need to enable this file to be executed by scripts.
Linux by defaults contrains execution permissions, type the following command while in /etc/systemd/system to see current permissions
```
ls -l mainPrgm.service
```
You should see something like this
```
-rw-r--r-- 1 root root 193 Nov  6 11:02 mainPrgm.service
```
Type the following command to change permissions
```
sudo chmod 777 mainPrgm.service 
```
If you type 
```
ls -l mainPrgm.service
```
You should now see something like this which means this script can now be read, written and executed by all users of the pi
```
-rwxrwxrwx 1 root root 193 Nov  6 11:02 mainPrgm.service
```

Type the following commands to enable the program to run on startup
```
sudo systemctl enable mainPrgm
sudo systemctl start mainPrgm
```
You should not get any feedback in the console


#### Script to control web browser
Switchcraft uses a web browser to load pages to display NFTs.
This web browser is controlled by Selenium which itself is controlled by our main python script, taking orders from the app, passing them to selenium which itself will display the right page in the web browser.
This part enables Selenium to run on startup.
As we will be editing the autostart file, we will also write the command to play a video while the Pi is booting

<!-- Type this command to open the file containing the list of programs to start on startup
This was replaced with sudo nano /etc/rc.local, leaving commented out because it also works but it has a small delay
```
sudo nano /etc/xdg/lxsession/LXDE-pi/autostart
```
add at the end:
```
@bash /home/pi/switchcraft_pi/execute.sh
```
press CTRL + X -> Y to save and close -->

Edit this file by typing:
```
sudo nano /etc/rc.local
```
At the end of the file but before the exit 0 line, add the following lines:
```
dmesg --console-off
sudo -u pi bash -c /home/pi/switchcraft_pi/execute.sh &
```
press CTRL + X -> Y to save and close 


We used to add omxplayer home/pi/switchcraft_pi/boot_assets/boot_video.mp4 after the execute.sh to boot on video.
However, OMXplayer is no longer supported by new Pi OS and VLC doesn't work on boot out of the box so need work to fix it.
replacement along the lines of
```
vlc -f ~/switchcraft_pi/boot_assets/boot_video.mp4 &
```

# Cleanup the Pi startup sequence so it boots nicely into SwitchCraft
Credit:
https://itnext.io/raspberry-pi-read-only-kiosk-mode-the-complete-tutorial-for-2021-58a860474215

install prerequisites
```
sudo apt-get install --no-install-recommends xserver-xorg x11-xserver-utils xinit openbox
```


## Disable starting logs and replace them with a boot video
Credit:
https://florianmuller.com/polish-your-raspberry-pi-clean-boot-splash-screen-video-noconsole-zram

### Rainbow screen
```
sudo nano /boot/config.txt
```
add the last line at very end
```
disable_splash=1
```
press CTRL + X -> Y to save and close

### change output of pi console
```
sudo nano /boot/cmdline.txt
```
In this file you will finde a string of parameters all in line 1. Its important that you add the following exactly at the end of the existing line 1, starting with a space between the exisitng and new. So lets add:
```
consoleblank=1 logo.nologo quiet loglevel=0 plymouth.enable=0 vt.global_cursor_default=0 plymouth.ignore-serial-consoles splash fastboot noatime nodiratime noram
```
press CTRL + X -> Y to save and close

### finish
```
sudo reboot
```
You should get a clean boot


## Debugging / tinkering
The Pi will now auto boot into a full screen kiosk mode with the NFTs you want to display
If you ever need to access the Pi, you can plug a Keyboard and hit ALT + F4 to exit the web browser
However, the Python scripts will continue running in the background. To shut them down find them using:
```
ps -ef | grep python
```

Then kill them using
```
sudo kill 9 <script number>
```

If everything works well, you will not see your mouse if plugging one to the Pi.
This is because of unclutter which is a program hiding the mouse called with the startup script.
If you want to disable it do the following:
```
sudo nano switchcraft_pi/execute.sh 
```
Change the line 
```
unclutter -idle 0 &
```
into 
```
# unclutter -idle 0 &
```
Exit (CTRL + X -> y)
Remove the # when you want to hide the mouse again
