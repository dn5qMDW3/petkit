# PetKit Integration for Home Assistant

[![HACS Validation](https://github.com/dn5qMDW3/petkit/actions/workflows/validate.yml/badge.svg)](https://github.com/dn5qMDW3/petkit/actions/workflows/validate.yml)
[![Lint](https://github.com/dn5qMDW3/petkit/actions/workflows/lint.yml/badge.svg)](https://github.com/dn5qMDW3/petkit/actions/workflows/lint.yml)

Custom Home Assistant integration for [PetKit](https://www.petkit.com/) smart pet devices.

## Supported Devices

| Category | Devices |
|----------|---------|
| **Feeders** | D3, D4, D4H, D4S, D4SH, FeederMini, Fresh Element (Solo/Gemini/Infinity) |
| **Litter Boxes** | T3, T4 (Pura MAX), T5, T6 (Pura X), T7 |
| **Water Fountains** | W5, CTW3 (Eversweet Solo 2/3 Pro) |
| **Air Purifiers** | K2, K3 (Pura Air) |

## Features

- Cloud polling with smart adaptive intervals
- MQTT real-time events (near-instant state updates)
- Camera/WebRTC streaming (Agora SDK, go2rtc, WHEP)
- BLE relay support
- 11 platforms: sensor, binary sensor, switch, button, number, select, fan, light, text, image, camera
- Media browser for camera snapshots and event recordings

## Installation

### HACS (Recommended)

1. Open **HACS** in Home Assistant
2. Click the three-dot menu → **Custom repositories**
3. Add `https://github.com/dn5qMDW3/petkit` with category **Integration**
4. Click **Add**, then find **PetKit** and click **Download**
5. Restart Home Assistant

### Manual

1. Download the [latest release](https://github.com/dn5qMDW3/petkit/releases/latest)
2. Extract `petkit.zip` into `<config>/custom_components/petkit/`
3. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for **PetKit**
3. Enter your PetKit account credentials and region

## Credits

- Architecture based on [Jezza34000/homeassistant_petkit](https://github.com/Jezza34000/homeassistant_petkit)
- API library: [pypetkitapi](https://github.com/Jezza34000/py-petkit-api)
- Litter events from [RobertD502/home-assistant-petkit](https://github.com/RobertD502/home-assistant-petkit)

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
