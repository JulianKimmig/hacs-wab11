# Home Assistant Configuration, Entity, and Service Contract

This document records the externally observable contract implemented by the
`hacs_wab11` custom component. The architectural ownership is described in
[`../ARCHITECTURE.md`](../ARCHITECTURE.md), and file/test ownership is mapped in
[`../code-relationships.md`](../code-relationships.md).

## Integration identity and compatibility

- Domain: `hacs_wab11`
- Display name: `Weishaupt WAB11`
- Integration type: local-polling hub
- Minimum Home Assistant version declared in `hacs.json`: `2025.1.0`
- Runtime dependency: `wab11==0.1.0`
- Config-flow version: `1`
- Device identifier: `(hacs_wab11, "<host>:<port>:<unit_id>")`
- Entity unique ID: `"<config-entry unique ID>_<entity key>"`

## Configuration flow

The user flow accepts the following config-entry data.

| Field     | Required | Default/constraint        | Meaning                                                                       |
| --------- | -------- | ------------------------- | ----------------------------------------------------------------------------- |
| `name`    | No       | String                    | Optional config-entry/device name; the host is used as the title when omitted |
| `host`    | Yes      | String                    | Controller host or IP address                                                 |
| `port`    | Yes      | `502`; integer `1..65535` | Modbus TCP port                                                               |
| `unit_id` | Yes      | `1`; integer `1..255`     | Modbus unit identifier                                                        |

Before entry creation, the integration constructs a five-heating-circuit
`WAB11Client`, performs `sync()`, and disconnects it in all outcomes. The
config-entry unique ID is `<host>:<port>:<unit_id>`, so Home Assistant rejects a
second entry with the same connection coordinates. Library connectivity and
timeout errors map to `cannot_connect`, validation errors to `invalid_config`,
and other library or unexpected errors to `unknown`.

The options flow stores a complete option set and Home Assistant reloads the
entry after it changes.

| Option                    | Default       | Constraint/effect                                                     |
| ------------------------- | ------------- | --------------------------------------------------------------------- |
| `main_scan_interval`      | `15` seconds  | Integer, minimum `5`; schedules main state polling                    |
| `energy_scan_interval`    | `300` seconds | Integer, minimum `60`; schedules energy polling                       |
| `enable_write_entities`   | `false`       | Loads select, number, and button platforms and permits runtime writes |
| `enable_energy_sensors`   | `true`        | Creates the three energy-total sensors                                |
| `enable_advanced_sensors` | `false`       | Creates the four advanced heat-pump temperature sensors               |

There is no YAML configuration path and no automatic discovery path in the
current integration.

## Entity contract

All entities are coordinator-backed, grouped under the entry's single WAB11
device, and use entity names composed by Home Assistant from the configured
device name and the names below.

### Baseline read entities

Sensors:

| Entity key              | Name                  | State                                                                       |
| ----------------------- | --------------------- | --------------------------------------------------------------------------- |
| `outdoor_temperature`   | Outdoor temperature   | Celsius temperature                                                         |
| `operating_state`       | Operating state       | Lowercase WAB11 operating-state enum name                                   |
| `error_code`            | Error code            | Integer code; raw sentinel `65535` becomes unavailable                      |
| `warning_code`          | Warning code          | Integer code; raw sentinel `65535` becomes unavailable; disabled by default |
| `hot_water_temperature` | Hot water temperature | Celsius temperature                                                         |
| `sg_ready_state`        | SG-Ready state        | `normal`, `evu_lock`, `recommended`, or `maximum`                           |

Binary sensors:

| Entity key              | Name                  | State/default                        |
| ----------------------- | --------------------- | ------------------------------------ |
| `has_error`             | Has error             | Problem boolean                      |
| `has_warning`           | Has warning           | Problem boolean; disabled by default |
| `hot_water_charging`    | Hot water charging    | Heat-active boolean                  |
| `secondary_heat_active` | Secondary heat active | Heat-active boolean                  |

### Optional read entities

When `enable_advanced_sensors` is true, the main coordinator supplies Celsius
sensors with keys `heat_pump_flow_temperature`,
`heat_pump_return_temperature`, `heat_pump_buffer_temperature`, and
`heat_pump_separator_temperature`.

When `enable_energy_sensors` is true, the energy coordinator supplies kWh
sensors with keys `total_energy_today`, `total_energy_month`, and
`total_energy_year`.

### Opt-in write entities

These platforms exist only when `enable_write_entities` is true. The runtime
checks the same option again before every operation.

- Select `system_mode` supports `automatic`, `heating`, `cooling`, `summer`,
  `standby`, and `second_heat`.
- Each configured heating circuit `N` receives select `hkN_mode`, supporting
  `automatic`, `comfort`, `normal`, `setback`, and `standby`.
- Each configured circuit receives `hkN_comfort_setpoint` and
  `hkN_normal_setpoint` numbers (`15..30 °C`, step `0.5`) plus
  `hkN_setback_setpoint` (`10..25 °C`, step `0.5`).
- `hot_water_normal_setpoint` accepts `30..65 °C`, step `1`;
  `hot_water_setback_setpoint` accepts `20..60 °C`, step `1`.
- `hot_water_push_minutes` accepts `0..240` minutes, step `5`.
- Buttons `trigger_hot_water_push` and `cancel_hot_water_push` start a
  30-minute push and cancel a push respectively.

Changing a write entity invokes the matching curated `wab11` client method and
publishes the returned main snapshot immediately. The integration assumes at
most five heating circuits and only creates circuit-specific entities for
circuits whose library model reports `is_configured`.

## Service contract

The integration registers these domain services idempotently during component
or entry setup. `entry_id` is optional for every service. It may be omitted
when exactly one WAB11 entry is loaded; with multiple loaded entries it is
required. An unknown ID, no loaded entry, or an ambiguous omitted ID raises a
`HomeAssistantError`. A selected entry with writes disabled also raises a
`HomeAssistantError`.

| Service                             | Fields                                                                                                                                      | Operation                               |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| `hacs_wab11.set_party_pause`        | `entry_id` optional; `circuit` required integer `1..5`; `mode` required `party` or `pause`; `hours` optional float `0.5..12`, default `2.0` | Activates party/pause for the circuit   |
| `hacs_wab11.cancel_party_pause`     | `entry_id` optional; `circuit` required integer `1..5`                                                                                      | Restores automatic party/pause behavior |
| `hacs_wab11.trigger_hot_water_push` | `entry_id` optional; `minutes` optional integer `0..240`, default `30`                                                                      | Starts a hot-water push                 |
| `hacs_wab11.cancel_hot_water_push`  | `entry_id` optional                                                                                                                         | Cancels a hot-water push                |

The executable schemas and routing live in
[`../../custom_components/hacs_wab11/__init__.py`](../../custom_components/hacs_wab11/__init__.py).
[`services.yaml`](../../custom_components/hacs_wab11/services.yaml) and the
translation files provide Home Assistant UI metadata for the same fields.
[`test_services.py`](../../tests/test_services.py) provides behavioral evidence
for all four operations and target-selection failures.

## Diagnostics contract

Config-entry diagnostics return `entry`, `options`, `main`, and `energy`
sections. `host`, `port`, and `unit_id` are redacted from `entry`. Coordinator
snapshots are recursively converted to JSON-compatible values: temperature
objects become Celsius numbers, datetimes become ISO-formatted strings, enums
become enum names, and dataclasses/collections are traversed. This behavior is
implemented by
[`diagnostics.py`](../../custom_components/hacs_wab11/diagnostics.py) and
exercised by [`test_diagnostics.py`](../../tests/test_diagnostics.py).
