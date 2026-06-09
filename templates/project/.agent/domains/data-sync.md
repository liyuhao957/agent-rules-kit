# Domain: Data, Sync, Migration, Backup

## Use When

Changing persistence, schema, sync, import/export, backup, deletion, privacy, data repair, migration, or cache behavior.

## Verify Before Editing

- Current models/schema and migration path.
- Read/write/delete call sites.
- Derived data, cache, sync, backup, import/export, and recovery paths.
- Tests or fixtures that cover the data path.

## Do

- Treat destructive changes as high risk.
- Check create, edit, delete, refresh, sync, restore, and conflict paths when touched.
- Preserve user data unless the user explicitly requested replacement or deletion.

## Do Not

- Assume old docs describe the current data model.
- Change migration or sync behavior without verifying related recovery/rollback implications.

## Done Means

Data state remains coherent across the affected lifecycle, and verification evidence or residual risk is explicit.

