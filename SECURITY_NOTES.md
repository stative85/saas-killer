# Security Notes

This repository includes local automation scripts that touch harvesting, content packaging, and upload workflows. Use a safety-first posture.

## Critical Handling Rules

- Never commit secrets, tokens, cookies, OAuth credentials, or app passwords.
- Keep local credential files out of git tracking.
- Treat browser-derived cookies as sensitive authentication material.
- Rotate credentials immediately if exposure is suspected.

## Known Risk Areas

- Some scripts currently assume local absolute paths.
- Some scripts include non-portable or hardcoded operational defaults.
- Generated artifacts and transcripts may contain private or sensitive data.

## Operator Guidance

- Run in a dedicated local environment.
- Validate paths and credentials before execution.
- Review outputs before sharing or publishing.
- Keep private media and generated bulk outputs outside tracked source by default.
