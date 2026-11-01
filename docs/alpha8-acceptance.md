# Alpha.8 weather and brand correction

This candidate fixes specific presentation defects. It is not the completed customer-experience redesign.

Weather uses the current weather entity condition, temperature and available humidity/wind information. Condition-specific Lucide icons replace Studio's fixed sun icon. Clear skies use a night presentation when the permitted home sun state says below horizon; phone-local hours never determine home daylight. No provider configuration or state is rewritten. Missing weather is explicit, with no sunny fallback. The last state-update timestamp is retained where supplied. Actual provider accuracy in the personal home has not been independently checked.

The native Android logo converter now skips SVG definitions and clipping paths. The original long logo contains a rectangular clip definition around its circular brand symbol; painting that definition was producing the square. Both Personal and Studio native paths are regenerated from their original source SVGs. The original circular brand symbol is preserved rather than replaced with a new trademark or copyright claim.

Validation: 221 isolated Python tests, source weather formatter tests, native compilation/signing and canonical asset verification. CI independently runs the full browser and pinned-Core contract suite. Physical phone rendering still requires acceptance.

Customer UX audit/redesign remains pending screenshot capture. The local browser integration reported disabled even after the user enabled it; the alternative automated Chromium capture request is pending. No screenshot-based audit or completed luxury redesign is claimed in this release.
