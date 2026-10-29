# Device onboarding — evaluation

Home Care → Add a device is available only to active administrators. A configured,
online ZHA or Zigbee2MQTT network is required; Studio does not install a broker,
configure USB passthrough, or automatically migrate an existing Zigbee network.

1. Choose an existing room and a ready network.
2. Review the destination and confirm the physical device is in pairing mode.
3. Start a 60-second admission window. Devices already known to the network are
   excluded from the new-device list.
4. Wait for the device's controls to finish discovery. Choose the controls and
   readings, then explicitly add them to the room. This saves the shared Studio
   layout without operating the device or changing Home Assistant areas.
5. Stop pairing. Additional devices can be assigned from the completed session,
   or a new reviewed session can be opened.

Closing the view does not extend or restart admission. The controller's original
60-second limit still applies. If an acknowledgement is lost, check status;
Studio does not replay the request. After a service restart, any unfinished
session is marked interrupted and must be explicitly closed before starting again.
The private journal is saved before radio admission. A damaged journal disables
pairing while leaving controls, accounts and recovery available.

## Installer scope

ZHA uses only `zha.permit` with duration 60 or 0 and an administrator context.
Zigbee2MQTT uses the configured MQTT integration: read-only bridge discovery,
an acknowledged health check before opening, and transaction-matched
`bridge/request/permit_join` requests. Commands are QoS 0 and never retained.
No generic MQTT publish, arbitrary radio service, network-key export, device
removal, force-leave or automatic re-pairing endpoint is exposed.

Single-level Zigbee2MQTT base topics are discovered automatically. A nested
base topic can be set in the Studio service's installer options. Inventory must
be known before admission. Networks exceeding 512 inventory entries require
installer review; the inventory is never silently truncated into a new-device
baseline. At most 64 new devices and 64 supported primary entities per device
are displayed. MQTT diagnostic entities are not selected automatically.

The adapter expects current Zigbee2MQTT JSON bridge state and
`interview_state` metadata. MQTT discovery must register device identifiers
containing their IEEE address. Unsupported devices or incomplete discovery stay
unready instead of receiving invented controls.

## Acceptance remaining

Automated policy, inert MQTT/service adapters and browser fixtures do not certify
a physical coordinator, radio range, device model, firmware, or Android TV remote.
The approved hardware catalogue remains empty until physical tests are recorded.
Device replacement and migration of automation references remain separate work.
This release is an evaluation candidate, not a production-certified release.

Protocol references: [Zigbee2MQTT bridge protocol](https://www.zigbee2mqtt.io/guide/usage/mqtt_topics_and_messages.html)
and [pinned ZHA service schema](https://github.com/home-assistant/core/blob/2026.10.4/homeassistant/components/zha/services.yaml).
