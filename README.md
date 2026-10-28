# Eufy RoboVac S1 Pro for Home Assistant

Experimental Home Assistant custom integration maintained in
SupaHotMoj0/ha-eufy-robovac-s1-pro. Not affiliated with Eufy, Anker,
Home Assistant, or HACS.

## Import status

This first commit initializes the repository only. The integration source,
HACS metadata, tests, and workflows have not yet been imported.
Do not install this repository until the full source import is complete.
No stable release or hardware-compatibility certification is claimed.

## Source and preservation requirements

The supplied eufy_robovac_s1_pro.zip.txt is a ZIP containing integration code.
Its manifest identifies tkoba1974/ha-eufy-robovac-s1-pro as upstream.
Preserve applicable upstream licenses, copyright notices, existing entity IDs,
and existing robot command payloads during import.

The supplied code logs local Tuya messages and integration command sends,
parses protobuf-style datapoints, and conditionally creates some entities
when known datapoints are present during setup. These mechanisms must not
be silently removed. They are not proof of a general command sniffer or
automatic identification of arbitrary new robot commands.

## Planned device-page experience

- Normal controls remain separate from developer diagnostics.
- Read-only diagnostic entities report observed datapoint counts,
  last-received update time, and bounded trace status.
- An opt-in developer capture switch enables a bounded, expiring trace.
  Metadata-only capture is the default; unknown payloads are not assumed safe.
- Trace records distinguish outgoing commands from this integration and
  incoming robot reports. They do not claim to intercept all app/cloud traffic.
- Known, validated capabilities can add their entities when datapoints first
  appear after startup, without duplicate entities or a Home Assistant restart.
- Unknown datapoints are observations, not automatically writable controls.
- Diagnostic downloads exclude passwords, tokens, local keys, account details,
  location/map data, and raw unknown payloads by default.

These are implementation requirements, not claims that these features are
already present in this first commit. A custom packet-inspector frontend
embedded in the stock device page is not promised.

## Validation and release gates

The prepared draft from the preceding review reported 38 focused offline
tests. Those results do not establish that this repository has run CI, booted
in Home Assistant, or successfully controlled a real S1 Pro.

Before a stable release: import and review the source, run the actual
Home Assistant/HACS validation workflows, complete third-party provenance
review, and test setup, reload, cleanup, late-arriving capabilities, and
robot commands against supported firmware.

Do not publish credentials or unredacted packet captures in GitHub issues.
