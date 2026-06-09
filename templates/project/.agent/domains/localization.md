# Domain: Localization

## Use When

Changing user-facing strings, language selection, locale-specific formatting, app metadata, screenshots, or translated assets.

## Verify Before Editing

- Current localization mechanism.
- Existing keys and fallback behavior.
- All supported language files or translation sources.
- Runtime surfaces that display the string.

## Do

- Prefer stable keys over hard-coded strings when the project supports localization.
- Keep translations natural, not literal or machine-like.
- Update all required language surfaces or clearly state what remains.

## Do Not

- Delete legacy keys without proving no call sites still use them.
- Assume every user-facing string is in the same localization system.

## Done Means

Relevant strings and language surfaces are consistent, or the final reply states exact uncovered locales/surfaces.

