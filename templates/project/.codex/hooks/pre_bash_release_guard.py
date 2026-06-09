#!/usr/bin/env python3
"""Lightweight PreToolUse hook reminder for high-risk shell commands.

Customize this script if you want command blocking. The default template only
prints a reminder because project release commands vary widely.
"""

import json
import sys

raw = sys.stdin.read()
try:
    payload = json.loads(raw) if raw.strip() else {}
except json.JSONDecodeError:
    payload = {}

text = json.dumps(payload, ensure_ascii=False).lower()
risky_words = ("deploy", "release", "publish", "push", "submit", "delete", "reset", "production", "prod")

if any(word in text for word in risky_words):
    print("Reminder: high-risk command detected. Verify scope, git state, auth, target, and live state first.")

