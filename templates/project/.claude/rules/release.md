---
paths:
  - ".github/workflows/**"
  - "fastlane/**"
  - "deploy/**"
  - "deployment/**"
  - "helm/**"
  - "terraform/**"
  - "Dockerfile"
  - "docker-compose*"
  - "ExportOptions.plist"
  - "**/*.entitlements"
  - "**/*Signing*"
  - ".releaserc*"
---

Release/external-state area: high risk. Before changing these files, read `.agent/domains/release.md` and follow `.agent/workflows/release.md`. Verify live state with real tools; do not infer it. Keep these globs mirrored with `.agent/drift-map.yml`.
