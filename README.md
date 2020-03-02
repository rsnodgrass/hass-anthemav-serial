# Anthem A/V Receivers (RS232 Serial Connection)

![Anthem Logo](https://github.com/rsnodgrass/hass-anthemav-serial/blob/master/anthemav.png?raw=true)

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=WREP29UDAMB6G)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
![beta_badge](https://img.shields.io/badge/maturity-Beta-yellow.png)

## Supported Hardware

Support for this integration is provided through the [Python anthemav_serial module](https://github.com/rsnodgrass/python-anthemav-serial) and supports Anthem models which communicate using Anthem's original RS232 serial Gen1 interface. For later models (while Anthem's Gen2 serial interface is still unsupported), the [Home Assistant IP-based anthemav integration](https://www.home-assistant.io/integrations/anthemav/) can be used. If someone wants to contribute and test the Gen2 RS232 integration, please feel free to contribute.

|  Model(s)                        | Series | RS232  | IP |
|  ------------------------------- | ------ |:------:|:--:|
|  Statement D2, D2v, D2v 3D       | d2     | **Gen1** | none |
|  Statement D1                    | d1     | **Gen1** | none |
|  AVM 20                          | avm20  | **Gen1** | none |
|  AVM 30                          | avm30  | **Gen1** | none |
|  AVM 50, AVM 50v                 | avm50  | **Gen1** | none |
|  MRX 300, MRX 500, MRX 700       | mrx    | **Gen1** | none |
|  AVM 60                          | avm60  | Gen2   | Gen2 |
|  MRX 310, MRX 510, MRX 710       | mrx1   | Gen2   | Gen2 |
|  MRX 520, MRX 720, MRX 1120      | mrx2   | Gen2   | Gen2 |
|  STR amplifiers                  | str    | Gen2   | Gen2 |

## Support

Visit the Home Assistant community if you need [help with installation and configuration of Anthem A/V receivers](https://community.home-assistant.io/t/anthem-line-of-receivers-and-pre-pros/1605/4).

This integration was developed to cover use cases for my home integration, which I wanted to contribute back to the community. Additional features beyond what has already been provided are the responsibility of the community to implement (unless trivial to add).

#### Versions

The 'master' branch of this custom component is considered unstable, alpha quality and not guaranteed to work.
Please make sure to use one of the official release branches when installing using HACS, see [what has changed in each version](https://github.com/rsnodgrass/hass-anthemav-serial/releases).

## Installation

### Step 1: Install

Make sure [Home Assistant Community Store (HACS)](https://github.com/custom-components/hacs) is installed,  then add the "Integration" repository: `rsnodgrass/hass-anthemav-serial`.

### Step 2: Configuration

Simplest configuration example:

```yaml
media_player:
  - platform: anthemav_serial
    series: d2
    port: /dev/ttyUSB0
```

In the case above, Home Assistant integration will automatically populate all the inputs and sources available on the Anthem series specified. For specific details on supported features for each Anthem model, [see the series configuration from anthemav_serial](https://github.com/rsnodgrass/python-anthemav-serial/tree/master/anthemav_serial/series).

More advanced configuration example:

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

To determine zones and source ids, check with the RS232 programming guide from Anthem for your amplifier model. Alternatively, these may be defined in [the series configuration from anthemav_serial](https://github.com/rsnodgrass/python-anthemav-serial/tree/master/anthemav_serial/series).

### Step 3: Add Lovelace Card

The following is a simplest Lovelace card which shows an interface to an Anthem receiver:

```yaml
type: media-control
entity: media_player.anthem_d2
```

Or use the [mini-media-player](https://github.com/kalkih/mini-media-player) for more control over source selection and other amplifiers features.

![Anthem Lovelace Examples](https://github.com/rsnodgrass/hass-anthemav-serial/blob/master/lovelace/mediaplayer.png?raw=true)

## See Also

* [Community support for Home Assistant integrations with Anthem A/V receivers](https://community.home-assistant.io/t/anthem-line-of-receivers-and-pre-pros/1605/4)
* [Home Assistant `anthemav` IP-based interface](https://www.home-assistant.io/integrations/anthemav/)
* [Anthem AVSForum support thread]()

## Known Issues

* AM/FM tuners are unsupported
* play, pause, prev, and next controls are unsupported

#### Future

* add "snapshot" state like Monoprice (save state to play doorbell, etc)
