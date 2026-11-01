# Alpha.7 interaction recovery

Development candidate, production certification remains false.

- Feedback is visible and operable above open native dialogs, and returns to the page when a dialog closes.
- Fast requests do not dismiss loading feedback for other pending work; critical errors are not replaced by old loading timers.
- Input error messages retain existing accessible help descriptions.
- Untouched editors and Restore buttons cannot overwrite saved drafts. Card identity and account scope isolate drafts; camel-case credential keys are excluded.
- Room editor drafts preserve the entire selection model, including devices hidden by filters. Explicit restoration does not publish a layout or actuate hardware.
- Personal room pages preserve cached controls/readings offline with actuators disabled.
- Completed integration sessions are reclaimed at capacity. An unsupported initial native form aborts only its newly created flow, avoiding orphan setup sessions.

Validation uses controlled browser failures/time, inert room-editor flows and isolated backend tests. Physical Zigbee, camera, notification and Android/TV acceptance gates remain as listed in release.json.
