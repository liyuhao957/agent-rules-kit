# Domain: Localization

## Use When

Changing user-facing strings, language selection, locale-specific formatting, app metadata, screenshots, or translated assets.

## Verify Before Editing

- Current localization mechanism and supported languages (record this project's setup here during adapt-rules).
- Existing keys, fallback behavior, and all language files or translation sources.
- Runtime surfaces that display the string — not every user-facing string is in the same localization system.

## Do

- Prefer stable keys over hard-coded strings when the project supports localization.
- Update all required language surfaces or clearly state what remains.
- Do not delete legacy keys without proving no call sites still use them.

## Done Means

Relevant strings and language surfaces are consistent, or the final reply states exact uncovered locales/surfaces.
