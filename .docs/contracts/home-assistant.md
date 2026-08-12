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
- Runtime dependency: `wab11==0.2.0`
- Config-flow version: `1`
- Device identifier: `(hacs_wab11, "<host>:<port>:<unit_id>")`
- Entity unique ID: `"<config-entry unique ID>_<entity key>"`

## Configuration flow

The user flow accepts the following config-entry data.

| Field                | Required | Default/constraint                        | Meaning                                                                       |
| -------------------- | -------- | ----------------------------------------- | ----------------------------------------------------------------------------- |
| `name`               | No       | String                                    | Optional config-entry/device name; the host is used as the title when omitted |
| `host`               | Yes      | String                                    | Controller host or IP address                                                 |
| `port`               | Yes      | `502`; integer `1..65535`                 | Modbus TCP port                                                               |
| `unit_id`            | Yes      | `1`; integer `1..255`                     | Modbus unit identifier                                                        |
| `n_heating_circuits` | No       | Integer `1..5`; omitted means auto-detect | Number of sequential heating-circuit register blocks                          |

Before entry creation, the integration constructs a `WAB11Client`, performs
`sync()`, and disconnects it in all outcomes. An explicit count is forwarded
unchanged. If the field is omitted, the library auto-detects sequential circuit
blocks up to five. Validation then persists the resulting positive integer as
`n_heating_circuits` in config-entry data in both cases. The library's exact
end-of-list and error-propagation rules are defined in the base package's
[`heating-circuit discovery contract`](../../../../.docs/contracts/heating-circuit-discovery.md).

The config-entry unique ID remains `<host>:<port>:<unit_id>` and does not
include the circuit count, so Home Assistant rejects a second entry with the
same connection coordinates. Library connectivity and timeout errors map to
`cannot_connect`, validation errors to `invalid_config`, and other library or
unexpected errors to `unknown`.

The options flow stores a complete option set and its update listener asks Home
Assistant's config-entry manager to reload the entry after it changes. The
manager owns the unload/setup state transitions; the listener does not invoke
the lifecycle functions directly.

| Option                    | Default                      | Constraint/effect                                                                          |
| ------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------ |
| `n_heating_circuits`      | Persisted config-entry value | Required integer `1..5`; overrides the detected/manual setup value after options are saved |
| `main_scan_interval`      | `15` seconds                 | Integer, minimum `5`; schedules main state polling                                         |
| `energy_scan_interval`    | `300` seconds                | Integer, minimum `60`; schedules energy polling                                            |
| `enable_write_entities`   | `false`                      | Loads select, number, and button platforms and permits runtime writes                      |
| `enable_energy_sensors`   | `true`                       | Creates the three energy-total sensors                                                     |
| `enable_advanced_sensors` | `false`                      | Creates the four advanced heat-pump temperature sensors                                    |

There is no YAML configuration path and no Home Assistant network/device
discovery source. The module-level `CONFIG_SCHEMA` uses Home Assistant's
`config_entry_only_config_schema` helper: an empty YAML configuration remains
valid, while a `hacs_wab11:` YAML section is logged as unsupported so the user
is directed to remove it.

At runtime, the options value takes precedence over config-entry data. For a
current entry, setup passes that effective integer explicitly to `Wab11Runtime`
and its `WAB11Client`. Changing the option reloads the entry, so manual
adjustments take effect on a newly constructed client without re-running
automatic detection.

For compatibility, an older entry that has neither the data field nor an
option passes `None` and auto-detects in its initial runtime refresh. While that
entry is loaded, the options form uses the resulting runtime collection length
as its editable default; it falls back to five only when no stored, overridden,
or loaded detected value is available. Saving the options persists an explicit
runtime count for subsequent reloads.

## Entity contract

All entities are coordinator-backed, grouped under the entry's single WAB11
device, and use entity names composed by Home Assistant from the configured
device name and the names below.

### Always-created sensors

These sensors use the main coordinator. “Disabled” means the entity is created
in the registry but disabled by default.

| Group                      | Entity keys                                                                                                | State / default                                                             |
| -------------------------- | ---------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| System                     | `outdoor_temperature`, `outdoor_temperature_2`                                                             | Primary and secondary Celsius readings                                      |
| System                     | `operating_state`                                                                                          | Lowercase `OperatingState` enum name                                        |
| System                     | `error_code`, `warning_code`                                                                               | Integer code; `65535` becomes unavailable; warning disabled                 |
| System                     | `power_request`                                                                                            | System power request in W                                                   |
| Hot water                  | `hot_water_temperature`, `hot_water_effective_setpoint`                                                    | Current and effective target temperatures in °C                             |
| Hot water                  | `hot_water_sg_ready_boost`, `hot_water_temperature_difference`                                             | SG boost and target-minus-current difference in K                           |
| Hot water diagnostics      | `hot_water_config`                                                                                         | Lowercase configuration enum; disabled                                      |
| Inputs                     | `sg_ready_state`                                                                                           | `normal`, `evu_lock`, `recommended`, or `maximum`                           |
| Secondary heat             | `wez2_status`, `wez2_operating_hours`, `wez2_switching_cycles`, `e1_operating_hours`, `e2_operating_hours` | Synchronized status/counters; hours/cycles use total-increasing state class |
| Secondary heat             | `secondary_heat_limit_temperature`, `bivalence_temperature_heating`, `bivalence_temperature_hot_water`     | Synchronized °C thresholds                                                  |
| Secondary heat derived     | `secondary_heat_total_operating_hours`                                                                     | Sum of WEZ2, E1, and E2 hours; total-increasing                             |
| Secondary heat diagnostics | `config_wez2`, `config_e1`, `config_e2`                                                                    | Synchronized integer configuration codes; disabled                          |

Each selected circuit whose synchronized `config` is not `NOT_CONFIGURED`
adds the following 13 sensors. Replace `N` with its one-based circuit number.

| Entity-key template                                                                                                | State / default                                                       |
| ------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------- |
| `hkN_room_effective_setpoint`, `hkN_room_temperature`, `hkN_flow_setpoint`, `hkN_flow_temperature`                 | Synchronized °C values                                                |
| `hkN_room_humidity`                                                                                                | Synchronized percentage; unavailable when the library value is `None` |
| `hkN_heating_curve`                                                                                                | Synchronized integer heating-curve value                              |
| `hkN_summer_winter_threshold`                                                                                      | Synchronized integer exposed with the current °C unit metadata        |
| `hkN_constant_temperature_heating`, `hkN_constant_temperature_heating_setback`, `hkN_constant_temperature_cooling` | Synchronized °C values                                                |
| `hkN_config`, `hkN_request_type`                                                                                   | Lowercase synchronized enum names; disabled                           |
| `hkN_party_pause`                                                                                                  | Synchronized encoded party/pause integer; disabled                    |

### Always-created binary sensors

| Entity keys                                                                                                                        | Source / default                                                           |
| ---------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `has_error`, `has_warning`                                                                                                         | Derived from synchronized system codes; warning disabled                   |
| `secondary_heat_active`, `wez2_active`, `electric_heater_1`, `electric_heater_2`                                                   | Derived from synchronized secondary-heat status and configuration; enabled |
| `sg_ready_1`, `sg_ready_2`, `input_h12`, `input_h13`, `input_h14`, `input_h15`, `input_de1`, `input_de2`                           | Synchronized digital input states; enabled                                 |
| `heat_pump_running`                                                                                                                | Derived from synchronized heat-pump power request; enabled                 |
| `heat_pump_error_free`, `heat_pump_heating`, `heat_pump_cooling`, `heat_pump_defrosting`, `heat_pump_hot_water`, `heat_pump_quiet` | Synchronized or derived heat-pump state; disabled                          |
| `system_heating`, `system_cooling`, `system_hot_water`, `system_defrosting`, `system_standby`                                      | Derived from synchronized system operating state; disabled                 |

### Option-gated sensors

When `enable_advanced_sensors` is true, the integration creates the full
synchronized heat-pump surface:

- Temperatures in °C: `heat_pump_flow_temperature`,
  `heat_pump_return_temperature`, `heat_pump_buffer_temperature`,
  `heat_pump_separator_temperature`, `heat_pump_evaporator_temperature`,
  `heat_pump_suction_gas_temperature`,
  `heat_pump_regenerative_flow_temperature`, and
  `heat_pump_sum_flow_temperature`.
- `heat_pump_operating_state` (lowercase enum),
  `heat_pump_power_request` (%), `heat_pump_temperature_spread` (K), and
  `heat_pump_power_heating`, `heat_pump_power_cooling`,
  `heat_pump_power_hot_water`, `heat_pump_power_defrost` (%).
- Disabled diagnostics/configuration sensors: `heat_pump_config`,
  `heat_pump_quiet_mode`, `heat_pump_start_mode`,
  `heat_pump_flow_rate_heating`, `heat_pump_flow_rate_cooling`, and
  `heat_pump_flow_rate_hot_water`.

When `enable_energy_sensors` is true (the default), all 16 synchronized kWh
values are exposed using `<category>_energy_<period>` keys, where category is
`total`, `heating`, `hot_water`, or `cooling` and period is `today`,
`yesterday`, `month`, or `year`. They use the energy coordinator and a
total-increasing state class.

### Deliberately unexposed model defaults

The integration does not expose `HeatingCircuit.status` or derived circuit
heating/cooling binary sensors, `HotWaterState.status` or a hot-water-charging
binary sensor, or `InputsState.config_*` configuration sensors. Those model
fields are not populated by the current `wab11` synchronization path; exposing
their defaults would report invented controller state. They remain visible in
diagnostics as model data, but must not be interpreted as synchronized values.

The exhaustive register/model/entity mapping, including units and raw
addresses, is in the root
[`variables reference`](../../../../docs/variables-reference.md).

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
publishes the returned main snapshot immediately. The effective selected or
detected count limits the runtime model collection to sequential circuits
`1..N`; the integration only creates circuit-specific entities among them
whose library model reports `is_configured`.

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

Diagnostics serialize the complete library snapshot, including model fields
that currently retain library defaults because no synchronization path reads
them. In particular, heating-circuit status, hot-water status, and input
configuration values in diagnostics are not evidence of controller state and
are deliberately not exposed as entities.
