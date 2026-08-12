# HACS WAB11 Architecture

This repository is a HACS-installable Home Assistant custom integration for the
Weishaupt WAB11 controller. The integration domain is `hacs_wab11`; Home
Assistant loads it from
[`custom_components/hacs_wab11`](../custom_components/hacs_wab11/), while
[`manifest.json`](../custom_components/hacs_wab11/manifest.json) declares it as
a local-polling hub with a config flow and a pinned `wab11==0.2.0` dependency.

## Runtime boundaries

```text
Home Assistant config entry
  -> integration lifecycle (__init__.py)
     -> Wab11Runtime (one wab11.WAB11Client and one asyncio lock)
        -> Wab11MainCoordinator -> main-state entities and write controls
        -> Wab11EnergyCoordinator -> energy entities
     -> global hacs_wab11 services -> selected loaded entry's Wab11Runtime
```

[`__init__.py`](../custom_components/hacs_wab11/__init__.py) owns config-entry
setup, reload, unload, platform forwarding, and service registration. Each
loaded entry receives one
[`Wab11RuntimeData`](../custom_components/hacs_wab11/coordinator.py) object in
`entry.runtime_data`. It contains the client wrapper, both coordinators, and
the exact platform list forwarded for that entry.

The config flow is the discovery boundary for new entries. A user may supply a
heating-circuit count from one through five. When the field is omitted,
validation lets the `wab11` client auto-detect sequential controller blocks.
Either result is persisted in config-entry data. The options flow exposes an
editable count override, and normal entry setup passes the effective persisted
integer to the runtime. Consequently, periodic polling and reloads of new
entries never repeat register-block discovery. For compatibility, an older
entry without the field passes `None` and detects during runtime; its options
form derives the editable default from the loaded client so saving the options
makes later runtimes explicit. The library-level detection invariant is owned
by the base package's
[`heating-circuit discovery contract`](../../../.docs/contracts/heating-circuit-discovery.md).

[`Wab11Runtime`](../custom_components/hacs_wab11/coordinator.py) is the only
integration layer that calls the standalone library client. Its single
`asyncio.Lock` serializes main refreshes, energy refreshes, and write actions
against the same Modbus connection. Main refreshes produce an immutable
`Wab11MainData` snapshot containing deep copies of the system, heating-circuit,
hot-water, heat-pump, secondary-heat, and input models. Energy refreshes return
a deep-copied `EnergyStatistics` model. A successful write similarly returns a
fresh main snapshot, which the entity or service handler immediately publishes
through the main coordinator.

The main coordinator polls at the configured main interval and translates
`WAB11Error` into Home Assistant `UpdateFailed`. The energy coordinator does
the same on its independent, slower interval and owns a per-entry
[`EnergyPowerEstimator`](../custom_components/hacs_wab11/power_estimator.py).
That estimator derives average power solely from the synchronized total-energy
today/yesterday counters; it does not consume heat-pump power request. The
energy coordinator always dispatches successful samples so held estimates can
be published even when the energy snapshot compares equal. Initial setup refreshes main
state before forwarding platforms and also requests an energy refresh. A main
refresh failure disconnects the client and leaves Home Assistant to retry the
entry. Successful unload disconnects only after all forwarded platforms unload.

## Platform ownership

The sensor and binary-sensor platforms are always forwarded. Select, number,
and button platforms are forwarded only when the `enable_write_entities`
option is true. Sensor creation is further controlled by the energy and
advanced-sensor options. The persisted count bounds which sequential circuit
models the runtime reads; heating-circuit entities are then created only for
models reported as configured in the first main snapshot.

The read surface is declarative. [`sensor.py`](../custom_components/hacs_wab11/sensor.py)
owns coordinator selection and entity construction;
[`sensor_descriptions.py`](../custom_components/hacs_wab11/sensor_descriptions.py)
owns system, hot-water, heat-pump, secondary-heat, and energy mappings; and
[`sensor_circuit_descriptions.py`](../custom_components/hacs_wab11/sensor_circuit_descriptions.py)
generates the repeated configured-circuit mappings. Descriptions expose only
values populated by the current library synchronizers, plus derived properties
whose inputs are populated. Model placeholders that are not synchronized—such
as heating-circuit status, hot-water status, and digital-input configuration
fields—are intentionally not entity sources.

All entities derive from
[`Wab11CoordinatorEntity`](../custom_components/hacs_wab11/entity.py). This
base binds availability and update handling to a coordinator, assigns all
entities from an entry to one Home Assistant device, and creates entity unique
IDs from the config-entry unique ID plus an entity key. Platform modules own
only entity descriptions/value conversion and write callbacks; they do not
communicate with Modbus directly.

The complete user-visible surface and option-dependent entity inventory are
recorded in the
[`Home Assistant contract`](contracts/home-assistant.md). Module, metadata, and
test ownership are mapped in [`code-relationships.md`](code-relationships.md).
The cross-package register/model/entity mapping is maintained in the root
[`variables reference`](../../../docs/variables-reference.md).

## Supporting boundaries

- [`config_flow.py`](../custom_components/hacs_wab11/config_flow.py) is the
  only configuration entry point. It verifies connectivity with a short-lived
  library client before creating an entry and supplies the options flow.
- [`diagnostics.py`](../custom_components/hacs_wab11/diagnostics.py) exposes
  config-entry data and current coordinator snapshots after redacting all
  connection coordinates.
- [`services.yaml`](../custom_components/hacs_wab11/services.yaml) and the
  service translations describe the UI, while schemas and routing behavior in
  [`__init__.py`](../custom_components/hacs_wab11/__init__.py) are executable
  enforcement.
- [`hacs.json`](../hacs.json), the component manifest, repository README, and
  GitHub workflows form the HACS/distribution boundary. See the
  [`validation and release workflow`](workflows/validation-release.md).

## Safety boundary

The controller connection is unauthenticated, unencrypted Modbus TCP. The
repository documents deployment on a direct or isolated network. Write
platforms default to disabled, and the runtime independently rejects every
write when that option is false, including calls made through globally
registered services. The integration exposes only the curated write methods
implemented by `Wab11Runtime`; it does not expose arbitrary register writes.
