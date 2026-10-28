# VAutomate occupancy and home-mode pack 0.1.0

**Lab drafts. Not installed, enabled, certified or connected to the customer app's Create flow.**

These seven native Home Assistant blueprints are generic templates. No household entity IDs, device IDs, credentials or personal automation YAML are copied into this pack. Their behavior was informed by a read-only review of room/bathroom entry/exit and scene/mode patterns; the original automations were kept unchanged.

| Template | Required choices | Included behavior |
| --- | --- | --- |
| Room entrance and exit | Presence/occupancy sensor, lights | Lights on after Off→On; off after two minutes of confirmed vacancy |
| Room exit lights off | Presence/occupancy sensor, lights | Lights off after three minutes of confirmed vacancy; never turns lights on |
| Bathroom entrance and exit | Presence/occupancy sensor, lights | Lights on for occupancy; five-minute vacancy delay; motion-only sensors excluded |
| Hallway motion lighting | Motion sensor, lights | Motion lighting with a two-minute no-motion delay; not marketed as proof of room vacancy |
| Bathroom ventilation | Humidity sensor, supported fans | Start above 65%; stop only below 55% for ten minutes; thresholds editable |
| Sunset curtains | Curtains | Close at sunset, with optional pause-mode guards |
| Dawat/Cinema/home modes | Mode helper, entry scene | Apply the chosen entry scene; optionally apply selected exit scenes |

Defaults are supplied so the normal configuration asks for entities. Timing, thresholds and pause-mode helpers are optional advanced choices. Selected entities still need capability checks and physical acceptance; a domain name alone does not certify a particular device.

The lighting and ventilation templates accept optional pause helpers, such as Cinema, Dawat, Sleep or manual hold. Helpers must all be known Off before a template acts. Missing or unavailable helpers block the rule. Lighting vacancy actions use explicit On→Off transitions and a sustained Off delay; Unknown/Unavailable is not interpreted as vacancy. Returning occupancy cancels the native pending vacancy timer.

**Motion is not occupancy.** A person sitting still or behind shower glass may not be detected. Bathroom templates require appropriate sensor coverage and stationary-occupant tests. A door contact is not used to infer that a room is empty. Keep accessible manual controls and a pause/hold option. These drafts do not claim automatic recognition of every manual lighting change.

Do not overwrite customer automations when adding or updating templates. The intended VAutomate flow remains: choose template → bind entities → review behavior and effects → explicitly approve creation → start paused unless enabling was explicitly selected. Importing a blueprint definition is different from creating an automation instance; native HA tools may enable an instance when it is saved. The VAutomate instance-creation adapter must handle approval and initial state before these appear as customer-ready templates.

No auto-disarm, unlock, camera recording, update installer, arbitrary action selector or external network request is included. This is not a life-safety, medical, emergency or access-control system.

Structural YAML checks do not prove HA runtime behavior. These drafts still need an isolated HAOS test, sensor-disconnect/restart tests, actual hardware checks, capability validation, approval/create integration, shared-home review and evidence before customer deployment. They are deliberately separate from the four already implemented time/day schedules.

Use only an isolated commissioning environment. No template was installed on the existing personal server. Do not ask customers to open the HA frontend to compensate for an unfinished VAutomate workflow.
