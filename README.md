# Weishaupt WAB11

Home Assistant custom integration for Weishaupt WAB11 heat pumps over Modbus TCP. It is structured for HACS installation and uses the standalone [`wab11`](https://github.com/JulianKimmig/wab11) Python library as its dependency.

## Safety

The WAB11 Modbus TCP interface is unencrypted. Use it only on a direct or isolated network segment, not on a general home LAN or any exposed network.

Write entities are disabled by default. The first release scope intentionally exposes only documented user-level controls such as system mode, heating-circuit modes, curated setpoints, party/pause, and hot-water push.

## Installation

1. Open HACS in Home Assistant.
2. Add this repository as a custom repository with type `Integration`.
3. Install `Weishaupt WAB11`.
4. Restart Home Assistant.
5. Add the integration from `Settings -> Devices & services`.

The integration installs the published `wab11==0.1.0` library from PyPI and requires Home Assistant 2025.1.0 or newer.

## Configuration

The config flow asks for:

- Host or IP address
- Port, default `502`
- Unit ID, default `1`

The options flow lets you change:

- Main polling interval
- Energy polling interval
- Whether write entities are enabled
- Whether energy sensors are enabled
- Whether advanced sensors are enabled

## Entity Scope

Read-only entities include:

- Outdoor temperature
- Operating state
- Error and warning code sensors
- Hot-water temperature
- SG-Ready state
- Secondary-heat activity
- Optional advanced heat-pump temperatures
- Optional energy totals

Writable entities include:

- `select` for system mode and configured heating-circuit modes
- `number` for heating-circuit setpoints
- `number` for hot-water setpoints and push duration
- `button` for triggering or cancelling hot-water push

Custom service actions:

- `hacs_wab11.set_party_pause`
- `hacs_wab11.cancel_party_pause`
- `hacs_wab11.trigger_hot_water_push`
- `hacs_wab11.cancel_hot_water_push`

## Data Updates

The main controller state is polled every 15 seconds by default. Energy statistics are polled every 300 seconds by default. Both intervals can be increased in the integration options. When the controller is temporarily unavailable, Home Assistant marks coordinator entities unavailable and retries on the next scheduled update.

## Known Limitations

- Communication uses unauthenticated, unencrypted Modbus TCP and must remain on an isolated network.
- Automatic network discovery is not available; the controller address must be entered manually.
- The integration models up to five heating circuits and only creates circuit entities for circuits reported as configured.
- Write controls are intentionally disabled until explicitly enabled in the integration options.

## Troubleshooting

- Confirm Home Assistant can reach the controller host and TCP port `502` from its own network namespace.
- Confirm the configured Modbus Unit ID, which defaults to `1`.
- If entities become unavailable, check the Home Assistant log for `hacs_wab11` and `wab11` messages, then verify the isolated network path to the controller.
- If write entities are missing, enable them in `Settings -> Devices & services -> Weishaupt WAB11 -> Configure`.

## Removal

Remove the config entry from `Settings -> Devices & services`, then uninstall `Weishaupt WAB11` in HACS. Restart Home Assistant after HACS removes the custom component files.

## Development

Use Python `3.13` to match the CI and Home Assistant test stack.

```bash
python -m pip install -r requirements_test.txt
pytest
ruff check .
mypy --ignore-missing-imports custom_components/hacs_wab11
```

## Repository Notes

The HACS workflow ignores GitHub repository description and topic checks because those are GitHub-side settings, not files inside the repository. Set the repo description/topics before removing that ignore if you want to prepare for inclusion in the default HACS catalog.
