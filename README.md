# Home Assistant SolaX Cloud Integration

A custom [Home Assistant](https://www.home-assistant.io/) integration that adds support for monitoring your SolaX inverter through the official SolaX Cloud API. Installable through [HACS](https://hacs.xyz/).

## Features

- Simple configuration via the Home Assistant UI (config flow)
- Polls the SolaX Cloud API every 5 minutes
- Exposes the full set of metrics provided by the SolaX Cloud API, including detailed PV, grid, battery and status statistics
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

### Why the serial number is required

The public SolaX Cloud API expects both the API token and the inverter serial number with every request. The serial number tells
the API which inverter's dataset should be returned for the supplied token. If it is omitted, SolaX simply rejects the request,
so the integration cannot fall back to token-only authentication. Entering the serial number during the config flow allows Home
Assistant to store the value once and send it automatically with every poll.

### Troubleshooting connection errors

If you receive the error message **„Verbindung zur SolaX Cloud API fehlgeschlagen“** even though the token and serial number are
correct, SolaX returned a generic error instead of the dedicated "token/serial does not match" message. In that case:

1. Double-check that the serial number was entered without spaces and matches the value in the SolaX Cloud portal (it is usually
   printed in upper-case letters).
2. Ensure the API token has not been regenerated recently. Each time you generate a new token in the portal, the previous token is
   invalidated.
3. Verify that the SolaX Cloud service is reachable from your Home Assistant host. Temporary outages or regional endpoints being
   unavailable also trigger the same error message. The integration automatically tries both the global (`www.solaxcloud.com`)
   and the European (`euapi.solaxcloud.com`) endpoints, so make sure outbound traffic to both hosts is allowed by your firewall.
4. Enable debug logging for `custom_components.solax_cloud` to collect the exact response returned by the API when opening an
   issue.

The integration validates the credentials during configuration and only creates the entry once a successful response is received.

## Disclaimer

This project is not affiliated with or endorsed by SolaX. Use at your own risk.

## Maintainer

- [404GamerNotFound](https://github.com/404GamerNotFound)
