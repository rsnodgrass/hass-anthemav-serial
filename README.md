# Anthem A/V Receivers (RS232 Serial Connection)

![Anthem Logo](https://github.com/rsnodgrass/hass-anthemav-serial/blob/master/anthemav.png?raw=true)

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=WREP29UDAMB6G)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

## Supported Hardware

Support for this integration is provided through the [Python anthemav_serial module](https://github.com/rsnodgrass/python-anthemav-serial) and supports Anthem models which communicate using Anthem's original RS232 serial Gen1 interface. For later models (while Anthem's Gen2 serial interface is still unsupported), the [Home Assistant IP-based anthemav integration](https://www.home-assistant.io/integrations/anthemav/) can be used.

|  Model(s)                        | Series       | RS232 Gen1 | RS232 Gen2 | IP |
|  ------------------------------- | ------------ |:----------:|:----------:|:--:|
|  Statement D2, D2v, D2v 3D       | ANTHEM_D2    | X |   |   |
|  Statement D1                    | ANTHEM_D1    | X |   |   |
|  AVM 20                          | ANTHEM_AVM20 | X |   |   |
|  AVM 30                          | ANTHEM_AVM30 | X |   |   |
|  AVM 50, AVM 50v                 | ANTHEM_AVM50 | X |   |   |
|  MRX 300, MRX 500, MRX 700       | ANTHEM_MRX   | X |   |   |
|  AVM 60                          | ANTHEM_AVM60 |   | X | X | 
|  MRX 310, MRX 510, MRX 710       | ANTHEM_MRX1  |   | X | X |
|  MRX 520, MRX 720, MRX 1120      | ANTHEM_MRX2  |   | X | X |
|  STR amplifiers                  | ANTHEM_STR   |   | X | X |


## Installation

Visit the Home Assistant community if you need [help with installation and configuration of Anthem A/V receivers](https://community.home-assistant.io/t/anthem-line-of-receivers-and-pre-pros/1605/4).

### Step 1: Install

Easiest installation is by setting up [Home Assistant Community Store (HACS)](https://github.com/custom-components/hacs), and then adding the "Integration" repository: rsnodgrass/hass-anthemav-serial.

#### Versions

The 'master' branch of this custom component is considered unstable, beta quality and not guaranteed to work. Please make sure to use one of the official release branches when installing using HACS, see [what has changed in each version](https://github.com/rsnodgrass/hass-anthemav-serial/releases).

### Step 2: Configure Sensors

Example configuration:

```yaml
media_player:
  - platform: anthemav_serial
    serial_port: /dev/ttyUSB0
```

More complex option:

```yaml
media_player:
  - platform: anthemav_serial
    serial_port: /dev/ttyUSB0
    baudrate: 115200
    model: d2
    protocol: anthem_gen1
```

protocol: anthem_gen1 (default), anthem_gen2, ip_gen2
baudrate: 9600 (default)

### Step 3: Add Lovelace Card

The following is a simplest Lovelace card which shows an interface to an Anthem receiver:

```yaml
```

![Anthem Lovelace Examples](https://github.com/rsnodgrass/hass-anthemav-serial/blob/master/lovelace/mediaplayer.png?raw=true)

## See Also

* [Community support for Home Assistant integrations with Anthem A/V receivers](https://community.home-assistant.io/t/anthem-line-of-receivers-and-pre-pros/1605/4)
* [Home Assistant `anthemav` IP-based interface](https://www.home-assistant.io/integrations/anthemav/)
* [Anthem AVSForum support thread]()

## Known Issues

* The tuner is currently unsupported as are the media_player play, pause, prev, and next controls.
* Only Zone 1 is currently supported
