---
paths:
  - "package.json"
  - "pnpm-lock.yaml"
  - "yarn.lock"
  - "package-lock.json"
  - "Project.swift"
  - "project.yml"
  - "Package.swift"
  - "Makefile"
  - "justfile"
  - "Gemfile"
  - "Podfile"
  - "pyproject.toml"
  - "Cargo.toml"
  - "go.mod"
  - ".github/workflows/**"
  - "scripts/**"
  - "test/**"
  - "tests/**"
  - "**/__tests__/**"
  - "**/*Tests/**"
  - "**/*.test.*"
  - "**/*.spec.*"
---

Build/test/CI area. Before changing these files, read `.agent/domains/build-test.md`; validation commands live in `.agent/command-contract.md`. Keep these globs mirrored with `.agent/drift-map.yml`.
