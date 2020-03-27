# Anthem A/V Receivers (RS232 Serial Connection)

![Anthem Logo](https://github.com/rsnodgrass/hass-anthemav-serial/blob/master/anthemav.png?raw=true)

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=WREP29UDAMB6G)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
![beta_badge](https://img.shields.io/badge/maturity-Beta-yellow.png)

## Supported Hardware

Support for this integration is provided through the [Python anthemav_serial module](https://github.com/rsnodgrass/python-anthemav-serial) and supports Anthem models which communicate using Anthem's original RS232 serial Gen1 interface. For later models (while Anthem's Gen2 serial interface is still unsupported), the [Home Assistant IP-based anthemav integration](https://www.home-assistant.io/integrations/anthemav/) can be used. If someone wants to contribute and test the Gen2 RS232 integration, please feel free to contribute.

|  Model(s)                        | Series | RS232    | IP |
|  ------------------------------- | ------ |:--------:|:--:|
|  Statement D2, D2v, D2v 3D       | d2     | **Gen1** | none |
|  Statement D1                    | d1     | **Gen1** | none |
|  AVM 20                          | avm20  | **Gen1** | none |
|  AVM 30                          | avm30  | **Gen1** | none |
|  AVM 50, AVM 50v                 | avm50  | **Gen1** | none |
|  MRX 300, MRX 500, MRX 700       | mrx    | **Gen1** | none |
|  AVM 60                          | avm60  | Gen2     | Gen2 |
|  MRX 310, MRX 510, MRX 710       | mrx1   | Gen2     | Gen2 |
|  MRX 520, MRX 720, MRX 1120      | mrx2   | Gen2     | Gen2 |
|  STR amplifiers                  | str    | Gen2     | Gen2 |

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
    name: "Theater Anthem D2v"
    series: d2v
    port: /dev/ttyUSB0
    baudrate: 115200
    scan_interval: 30

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

Notes about the above configuration:

* Specifying the zones explicitly allows limiting how many media player instances are created (otherwise one for each of the three zones is created).
* The default baud rate is based on the series model. If you change the baud rate in HASS, you must also change it in the setup menu on your Anthem device.

To determine zones and source ids, check with the RS232 programming guide from Anthem for your amplifier model. Alternatively, these may be defined in [the series configuration from anthemav_serial](https://github.com/rsnodgrass/python-anthemav-serial/tree/master/anthemav_serial/series).

### Step 3: Add Lovelace Card

The following is a simplest Lovelace card which shows an interface to an Anthem receiver:

```yaml
type: media-control
entity: media_player.anthem_d2
```

Or use the [mini-media-player](https://github.com/kalkih/mini-media-player) for more control over source selection and other amplifier features.

![Anthem Lovelace Examples](https://github.com/rsnodgrass/hass-anthemav-serial/blob/master/lovelace/mediaplayer.png?raw=true)

## See Also

* [Community support for Home Assistant integrations with Anthem A/V receivers](https://community.home-assistant.io/t/anthem-line-of-receivers-and-pre-pros/1605/4)
* [Home Assistant `anthemav` IP-based interface](https://www.home-assistant.io/integrations/anthemav/)
* [Anthem AVSForum support thread]()

## Known Issues

* play, pause, prev, and next controls are unsupported
* AM/FM tuners are unsupported (though this would be useful during Internet outages).  One simple idea (compared to implementing a tuner) is to have presets like the following has been considered (with a select_preset service or create an input_select listing all presets with callback):

```yaml
media_player:
  - platform: anthemav_serial
    series: d2v

    presets:
      "Public Radio (KUOW)": { fm: 94.9 }
      "CBC Radio One":       { am: 690 }
      "KEXP":                { fm: 90.3 }
      "KISS FM":             { fm: 106.1 }
      "KUBE Hip Hop":        { fm: 93.3 }
      "KISW Rock":           { fm: 99.9 }
```

This would not be hard to implement as the underlying anthemav_serial library already supports `send_command('fm_tune' { 'channel': 94.9 })`. Rather than input_select, the presets could also just be exposed as sources (which would make it easier to apply to all zones) and auto-populated in the sources for each zone.


#### Future

* add "snapshot" state like Monoprice (save existing state to play doorbell and then restore)
