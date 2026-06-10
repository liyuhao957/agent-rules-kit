---
paths:
  - "db/**"
  - "prisma/**"
  - "drizzle/**"
  - "supabase/migrations/**"
  - "**/models/**"
  - "**/Models/**"
  - "**/schema/**"
  - "**/Schema/**"
  - "**/migrations/**"
  - "**/Migrations/**"
  - "**/stores/**"
  - "**/Stores/**"
  - "**/*.sql"
  - "**/*.xcdatamodeld/**"
---

Data/persistence area. Before changing these files, read `.agent/domains/data-sync.md` and verify its claims against current code. Destructive paths are high risk. Keep these globs mirrored with `.agent/drift-map.yml`.
