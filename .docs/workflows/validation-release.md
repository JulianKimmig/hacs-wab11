# Validation and Release Workflow

This record describes the validation and release automation currently present
in the HACS WAB11 repository. Architecture and public behavior are documented
in [`../ARCHITECTURE.md`](../ARCHITECTURE.md) and
[`../contracts/home-assistant.md`](../contracts/home-assistant.md).

## Local validation

The repository targets Python 3.13 for its CI/Home Assistant test stack. Local
environments used to investigate lifecycle behavior must also use Python 3.13
and be freshly resolved from `requirements_test.txt`; reusing a Python 3.12
environment can retain an older Home Assistant config-entry state machine.
[`requirements_test.txt`](../../requirements_test.txt) installs the Home
Assistant custom-component test plugin and the same `wab11==0.2.0` version
pinned by the component manifest. The commands mirrored by CI are:

```bash
python -m pip install -r requirements_test.txt
ruff check .
ruff check --select I .
ruff format --check .
mypy --ignore-missing-imports custom_components/hacs_wab11
pytest
```

[`setup.cfg`](../../setup.cfg) configures pytest with automatic asyncio support
and coverage of `custom_components.hacs_wab11`. The coverage report shows
missing lines and fails below 100%. Tests use the real Home Assistant config
flow, config-entry, entity-service, custom-service, and diagnostics surfaces.
Only the external Modbus connection is replaced by the register-backed test
connection in [`tests/conftest.py`](../../tests/conftest.py), using
[`tests/fixtures/fake_system.json`](../../tests/fixtures/fake_system.json).
The implementation-to-test mapping is maintained in
[`../code-relationships.md`](../code-relationships.md).

Circuit-count integration behavior is exercised by
[`tests/test_config_flow.py`](../../tests/test_config_flow.py), which covers an
explicit setup value, omission with detected-count persistence, and editing the
effective count through options. [`tests/test_init.py`](../../tests/test_init.py)
verifies that entry setup constructs the runtime library client with the
effective persisted value. The upstream probing and Modbus exception-code
rules are tested in the base package and documented in its
[`heating-circuit discovery contract`](../../../../.docs/contracts/heating-circuit-discovery.md).

`requirements_dev.txt` adds Home Assistant, Ruff, and mypy for broader local
development. The repository also has a separate
[`pre-commit configuration`](../../.pre-commit-config.yaml) for file hygiene,
Ruff linting/import sorting/formatting, and Prettier.

## Pull-request and main-branch validation

All three validation workflows run on every pull request and on pushes to
`main`:

1. [`ci.yaml`](../../.github/workflows/ci.yaml) checks out the repository, uses
   Python 3.13, installs `requirements_test.txt`, and runs Ruff lint, import,
   formatting, mypy, and pytest gates.
2. [`hacs.yaml`](../../.github/workflows/hacs.yaml) runs `hacs/action@main` in
   the `integration` category. It ignores the repository description and topic
   checks because those values are GitHub-side metadata rather than repository
   files.
3. [`hassfest.yaml`](../../.github/workflows/hassfest.yaml) runs Home
   Assistant's Hassfest action, which validates integration metadata and
   Home Assistant repository conventions. In particular, the manifest keeps
   `domain` and `name` first and all remaining keys alphabetical, and the
   integration declares its config-entry-only YAML schema because it exposes
   `async_setup` for service registration.

The HACS-facing inputs to those checks include
[`hacs.json`](../../hacs.json),
[`custom_components/hacs_wab11/manifest.json`](../../custom_components/hacs_wab11/manifest.json),
[`README.md`](../../README.md), [`info.md`](../../info.md), translation/service
metadata, and the component layout.

## Release behavior

[`release.yaml`](../../.github/workflows/release.yaml) runs only when a tag
matching `v*` is pushed. It checks out the tagged repository and creates a
GitHub release with generated release notes through
`softprops/action-gh-release@v2`. It does not build or attach a separate
artifact and does not invoke the CI, HACS, or Hassfest commands itself.

The installable release is therefore the tagged repository content consumed by
HACS. The component version and runtime dependency are declared in
[`manifest.json`](../../custom_components/hacs_wab11/manifest.json), while the
minimum Home Assistant version is declared in [`hacs.json`](../../hacs.json).
Any release preparation that changes those compatibility facts must keep the
public contract and these metadata files aligned before the `v*` tag is
created.
