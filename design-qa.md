# Personal-aligned Studio interface QA

Date: 2026-11-01. Scope: alpha.9 interface and Personal 0.2.4 weather/theme release. This is software/interface acceptance, not commercial hardware certification.

## Visual truth and capture setup

The user selected their existing Personal dashboard as the design reference. Original, unmodified captures remain outside this repository under `../../work/personal-studio-refresh/` to avoid publishing household information.

- Source: `02-personal-reference.jpg`, 1265 x 712 pixels, browser CSS viewport 1265 x 712.
- Studio full view: `09-studio-wide-final.jpg`, 1265 x 712 screenshot pixels, browser reported CSS viewport 1280 x 720. The browser screenshot surface normalizes its capture to approximately 0.988 pixels per CSS pixel. No content was redrawn.
- Side-by-side evidence: `11-personal-studio-comparison.jpg`. Source retained at original size; Studio normalized to the source frame for comparison. Real Personal home versus explicitly simulated Studio showroom; identical household content is intentionally not copied.
- Phone: `04-studio-phone-night.jpg`, `06-studio-phone-rooms-final.jpg`, 390 x 844. No horizontal overflow.
- Installed lab: `08-installed-studio-home.jpg`, 664 x 651. Actual alpha.9 backend with existing synthetic test home, not a fabricated customer installation.
- Published Personal entry: `10-personal-root-final.jpg`. All scripts resolve to the coherent versioned www release.

Full-view comparison was inspected as a combined image. Separate focused crops were unnecessary: weather, heading, logo, sidebar and people/security surfaces are legible in these full captures, with phone screenshots separately checking wrapping.

## Findings and comparison history

1. [P1, fixed] Studio originally had a different green palette, plain heading hierarchy and sparse room presentation. Replaced with Personal-aligned serif headings, neutral glass cards, centered official wordmark, compact controls and people/security grouping. Before: `01-studio-rooms-before.jpg`. After: `09-studio-wide-final.jpg`, `06-studio-phone-rooms-final.jpg`.
2. [P1, fixed] Sunny could persist after dark when the provider omitted or lagged its daylight flag. Home sun state is authoritative, then home-location solar calculation, then explicit provider flag. Unknown/offline states do not invent sunny weather. Night fixture and day/night unit cases passed. Live Personal Details identifies the actual daylight source without exposing coordinates.
3. [P2, fixed] Phone heading action crowded the room title. Moved the action above the heading; the final 390px capture has clear wrapping and even room cards.
4. [P2, fixed] Closed mobile drawer cast a residual shadow into Ivory content. Removed shadow while closed; retained glass and shadow when open. Final stylesheet is included in the installed source hash comparison.
5. [P2, fixed] Old www entry and cached assets could retain earlier interfaces. Published a coherent Personal release and stamped Studio asset URLs with the release version. Original root URL remains valid, preserving authentication origin and native path policy.
6. [P2, fixed] Decorative Personal weather layer intercepted the Details button. Disabled decorative pointer events and verified the modal opens live.

## Required fidelity surfaces

- Typography: Georgia display headings and existing system sans body text follow Personal hierarchy. Phone room headings wrap without card misalignment; long names remain within their tiles. Native browser antialiasing retained; no screenshot claim of exact font rasterization across devices.
- Layout rhythm: compact room tiles, consistent radii, aligned weather/people panels, slim collapsible desktop rail and hidden phone drawer. Studio uses two context columns on wide screens; Personal keeps its configurable existing layout. This is an intentional product adaptation, not a pixel clone.
- Color tokens: Jet Black, Ivory, Deep teal and neutral Obsidian. Checked Ivory logo contrast and immediate theme updates. Current selections are device-local and persist immediately.
- Assets: existing official long/short vector logos retained. Weather uses pinned Lucide paths and licensed SunCalc code. No replacement logo or emoji imitation introduced.
- Copy: familiar Home, Rooms, Routines, Home Care and Manage home labels. Commissioning notice appears in administrative care/setup routes; operational offline/error warnings remain visible everywhere relevant.

## Interaction checks

- Personal: Ivory applied immediately, modal closed without discard prompt, reload retained it without Save, then Jet Black restored.
- Studio: all four themes selected through the UI; installed lab body changed immediately to sand and jet. Ivory official logo remains visible.
- Sidebar: phone open/close, wide compact rail and whole-room navigation checked.
- Inert showroom only: room master light toggle changed on/off and retained exactly the same card bounding rectangle and keyboard focus. No Personal device service was called.
- Full Personal device/integration workspace opened read-only from the versioned assets.
- Installed lab source: all 32 files match the final package. Existing rooms, shared home, paused automations and administrator/member permissions passed the commissioning contract.
- Browser console: no captured errors on Personal, installed Studio or inert showroom in the checked flows.

## Remaining coverage

Physical phone/TV motion, camera codec behavior and actual Zigbee hardware certification still require device testing. Desktop/phone browser captures do not substitute for those tests. The lab has no weather provider; nighttime rendering was verified in the explicitly inert showroom and automated tests, without modifying the Personal sun entity or adding fake lab weather.

## Implementation checklist

- [x] Align Studio visual language with selected Personal reference.
- [x] Correct daylight precedence and local solar fallback.
- [x] Keep immediate theme selection across editions.
- [x] Verify phone wrapping, stable room toggle geometry and sidebar.
- [x] Publish full Personal www entry while preserving Home Control hashes.
- [x] Verify signed Android assets and installed lab source.

Follow-up polish: physical-device animation review on the user's S23 Ultra and TV. No actionable P0/P1/P2 issue remains in the checked interface scope.

Historical alpha.9 result: passed


## Alpha.10 everyday management follow-up

The requested flow is Manage home -> Rooms -> create/edit/remove -> Devices -> Zigbee connections, plus a member-only local dashboard editor. Browser interaction returned unavailable before fresh captures could be made. No new screenshot audit is claimed for alpha.10; alpha.9 images above are historical context only.

Implemented changes: compact management task rows and primary Add a device action; everyday device filtering by default with an explicit administrator system-entity switch; room removal also removes that room's shortcut cards; linked-routine failures offer Review linked routines; server-side member checks exclude diagnostic/configuration controls and unapproved helpers; non-admin local presentation editing is scoped by home profile and account and never publishes layout or edits device assignments. Local presentation changes intentionally do not sync to another device. Administrators continue publishing the common starting dashboard.

Validation includes pure view isolation/filtering tests and browser regression coverage for room/card removal and member dashboard controls. Current limitations: physical USB coordinator not detected by Windows; no pairing success or fresh live visual acceptance claimed. Complete the browser capture and physical coordinator tests when these surfaces are available.

Final result: blocked

Blocker: fresh browser-rendered alpha.10 design evidence is unavailable. Software checks and installation results must be reported separately from this visual acceptance status.


Alpha.10 automated render inspection: successful private CI run 41311486600 supplied a fresh 390px full-page management-phone.png, saved locally at ../../work/studio-ease-qa/management-phone.png and inspected. It shows compact task rows, a primary Add a device action, readable wrapping and no overflow. This is a simulated home rendered by Chromium, not a live HAOS capture. The member screenshot from that run was rejected because it captured the arrival animation; its test now waits for the intro to detach before capture. The live test-server API separately passed room/card removal, exact restoration of the original shared home, administrator/member permissions and all 32 installed source hashes. 226 backend tests passed in CI.

Manual live visual acceptance remains blocked by browser interaction availability. USB commissioning remains blocked by no detected host or guest serial coordinator. No successful physical pairing is claimed.
