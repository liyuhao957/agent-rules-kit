# Domain: Data, Sync, Migration, Backup

## Use When

Changing persistence, schema, sync, import/export, backup, deletion, privacy, data repair, migration, or cache behavior.

## Verify Before Editing

- Current models/schema and migration path (record this project's data lifecycle here during adapt-rules).
- Read/write/delete call sites; derived data, cache, sync, backup, import/export, and recovery paths.
- Tests or fixtures that cover the data path.

## Do

- Treat destructive changes as high risk; preserve user data unless the user explicitly requested replacement or deletion.
- Check create, edit, delete, refresh, sync, restore, and conflict paths when touched.
- Verify recovery/rollback implications before changing migration or sync behavior.

## Done Means

Data state remains coherent across the affected lifecycle, and verification evidence or residual risk is explicit.
