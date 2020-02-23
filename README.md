# Anthem A/V Receivers (RS232 Serial Connection)

![Anthem Logo](https://github.com/rsnodgrass/hass-anthemav-serial/blob/master/anthemav.png?raw=true)

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=WREP29UDAMB6G)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

## Supported Hardware

Support for this integration is provided through the [Python anthemav_serial module](https://github.com/rsnodgrass/python-anthemav-serial) and supports Anthem models which communicate using Anthem's original RS232 serial Gen1 interface. For later models (while Anthem's Gen2 serial interface is still unsupported), the [Home Assistant IP-based anthemav integration](https://www.home-assistant.io/integrations/anthemav/) can be used.

|  Model(s)                        | Series | RS232  | IP |
|  ------------------------------- | ------ |:------:|:--:|
|  Statement D2, D2v, D2v 3D       | d2     | **Gen1** | none |
|  Statement D1                    | d1     | **Gen1* *| none |
|  AVM 20                          | avm20  | **Gen1** | none |
|  AVM 30                          | avm30  | **Gen1** | none |
|  AVM 50, AVM 50v                 | avm50  | **Gen1** | none |
|  MRX 300, MRX 500, MRX 700       | mrx    | **Gen1** | none |
|  AVM 60                          | avm60  | Gen2   | Gen2 | 
|  MRX 310, MRX 510, MRX 710       | mrx1   | Gen2   | Gen2 |
|  MRX 520, MRX 720, MRX 1120      | mrx2   | Gen2   | Gen2 |
|  STR amplifiers                  | str    | Gen2   | Gen2 |


## Installation

Visit the Home Assistant community if you need [help with installation and configuration of Anthem A/V receivers](https://community.home-assistant.io/t/anthem-line-of-receivers-and-pre-pros/1605/4).

### Step 1: Install

Easiest installation is by setting up [Home Assistant Community Store (HACS)](https://github.com/custom-components/hacs), and then adding the "Integration" repository: rsnodgrass/hass-anthemav-serial.

NOTE: The 'master' branch of this custom component is considered unstable, beta quality and not guaranteed to work. Please make sure to use one of the official release branches when installing using HACS, see [what has changed in each version](https://github.com/rsnodgrass/hass-anthemav-serial/releases).

### Step 2: Configuration

Example configuration:

```yaml
media_player:
  - platform: anthemav_serial
    series: d2
    port: /dev/ttyUSB0
```

In the case above, Home Assistant integration will automatically populate all the inputs and sources available on the Anthem series specified. For specific details on supported features for each Anthem model, [see the series configuration from anthemav_serial](https://github.com/rsnodgrass/python-anthemav-serial/tree/master/anthemav_serial/series).

Additional configuration:

```yaml
media_player:
  - platform: anthemav_serial
    series: avm50
    port: /dev/ttyUSB0
    name: "Anthem AVM50v"
    baudrate: 115200

    zones:
      1:
        name: "Home Theater"

    sources:
      1:
        name: "Fire TV"
      2:
        name: "Broadcast TV"
      3:
        name: "Sonos"
```

Where source key maps to the appropriate source id for the configured Anthem series, e.g.:

| Id | Anthem Source Name |
|:--:| ------------------ | 




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

#### Future

* add "snapshot" state like Monoprice (save state to play doorbell, etc)
