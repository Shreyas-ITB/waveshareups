# waveshareupsbattery
Waveshare UPS Hat (C) for Raspberry PI Zero Plugin

A pwnagotchi plugin for a battery display in percentage

UPS HAT FROM WAVESHARE:
https://www.waveshare.com/ups-hat-c.htm
https://www.waveshare.com/wiki/UPS_HAT_(C)

(don't forget to turn on I2C on your raspberry pi)

USED IMAGE: 
https://github.com/wpa-2/pwnagotchi/releases


If you are using the Waveshare UPS HAT for the Raspberry Pi Zero, 
this plugin allows you to display the battery percentage on your pwnagotchi.

The plugin has been tested on a Pwnagotchi with the 1.5.5FIX image and the Waveshare Display V2. 
Although it has not been tested on displays of other generations, the code can potentially be adapted if needed. 


www.pwnagotchi.ai/plugins/ provides instructions on how to install plugins. 
You can also save the python file in /usr/local/share/pwnagotchi/installed-plugins/ 
and add the following line to config.toml in /etc/pwnagotchi/: "main.plugins.wavesharebattery.enabled = true". 
The battery typically lasts around 2.5-3 hours and charges quickly.

----------------------------------------
- Configuration
-- Under ``config.toml``
  ```
  main.plugins.waveshareups.enabled = true
  main.plugins.waveshareups.shutdown = 15 # shuts down at 15 percent battery
  main.plugins.waveshareups.pwr_x_coord = 140
  main.plugins.waveshareups.pwr_y_coord = 0
  main.plugins.waveshareups.ups_x_coord = 140
  main.plugins.waveshareups.ups_y_coord = 0
  main.plugins.waveshareups.battery_capacity = 1000 # in mah (milli amp hours)
  ```
