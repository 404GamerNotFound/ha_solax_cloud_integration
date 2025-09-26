# Home Assistant SolaX Cloud Integration

A custom [Home Assistant](https://www.home-assistant.io/) integration that adds support for monitoring your SolaX inverter through the official SolaX Cloud API. Installable through [HACS](https://hacs.xyz/).

## Features

- Simple configuration via the Home Assistant UI (config flow)
- Polls the SolaX Cloud API every 5 minutes
- Exposes all numeric metrics provided by the SolaX Cloud API, including detailed PV, grid and battery statistics
- Designed to work entirely through the cloud API (no local network connection required)

## Installation

1. Ensure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance.
2. Add this repository as a custom repository in HACS (category: Integration).
3. Install the **SolaX Cloud** integration from HACS and restart Home Assistant if prompted.
4. In Home Assistant, go to **Settings → Devices & Services** and add the **SolaX Cloud** integration.

## Configuration

During configuration you will be asked for:

- **Token ID** – available from the SolaX Cloud portal under *User Center → API Management*.
- **Inverter serial number** – the serial number of the inverter registered in SolaX Cloud.

Both pieces of information are required by the SolaX Cloud API, as documented by SolaX. The integration validates the credentials before creating the entry.

## Disclaimer

This project is not affiliated with or endorsed by SolaX. Use at your own risk.

## Maintainer

- [404GamerNotFound](https://github.com/404GamerNotFound)
