# Anthem A/V Receivers (RS232 Serial Interface)

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=WREP29UDAMB6G)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

## Supported Hardware



For the following devices, it is recommended to use the [`anthemav` IP-based interface](https://www.home-assistant.io/integrations/anthemav/):

* [MRX 520](https://www.anthemav.com/products-current/series=mrx-series-gen3/model=mrx-520/page=overview), [MRX 720](https://www.anthemav.com/products-current/collection=performance/model=mrx-720/page=overview), [MRX 1120](https://www.anthemav.com/products-current/collection=performance/model=mrx-1120/page=overview), and [AVM 60](https://www.anthemav.com/products-current/model=avm-60/page=overview)
* [MRX 310](https://www.anthemav.com/products-archived/type=av-receiver/model=mrx-310/page=overview), [MRX 510](https://www.anthemav.com/products-archived/series=mrx-series/model=mrx-510/page=overview), [MRX 710](https://www.anthemav.com/products-archived/type=av-receiver/model=mrx-710/page=overview)

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
    tty: /dev/ttyUSB0
```

{% configuration %}
tty:
  description: The serial tty used to connect to the device.
  required: true
  type: string
name:
  description: The name of the device used in the frontend.
  required: false
  type: string
{% endconfiguration %}

### Step 3: Add Lovelace Card

The following is a simplest Lovelace card which shows an interface to an Anthem A/V receiver:

```yaml
```

![Anthem Lovelace Examples](https://github.com/rsnodgrass/hass-anthemav-serial/blob/master/lovelace/mediaplayer.png?raw=true)

## See Also

* [Community support for Home Assistant integrations with Anthem A/V receivers](https://community.home-assistant.io/t/anthem-line-of-receivers-and-pre-pros/1605/4)
* [Home Assistant `anthemav` IP-based interface](https://www.home-assistant.io/integrations/anthemav/)

## Known Issues

