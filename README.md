# 🐺 SAAS KILLER

A closed-loop narrative engine that ingests raw speech, repairs it, extracts signal, compiles high-resonance scripts, renders media, and deploys to YouTube with feedback-driven evolution.

## ⚠️ Operational Status (Read First)

- This repository is a Windows-first local project and currently mixes source code with generated artifacts.
- Runtime behavior is validation-in-progress; several scripts depend on local environment assumptions.
- Treat this as an operator toolchain, not a one-command production deployment package.

## 🏛️ Pipeline

1. **Ingest**
   * Parallel harvest of transcripts (YouTube / Reels)
2. **Repair**
   * Subtitle normalization and artifact removal (Forensic Subtitle Forge)
3. **Index**
   * Chunking, scoring, and obsession term extraction
4. **Evolve**
   * Script generation (multi-mode)
   * A/B scoring + bidirectional bias shaping
5. **Render**
   * Neural TTS (Edge) + FFmpeg packaging
6. **Deploy**
   * YouTube private upload + manifest tracking
7. **Learn**
   * Feedback ingestion -> bias updates -> next run improvement

## 🏎️ Modes

* `fracture_aggressive` -> conceptual, dense, internal signal
* `retention_aggressive` -> fast, direct, audience-optimized

## 🧬 Hook System

Hooks are extracted, ranked, and tested across:
* **Declarative:** Stable, safe, internally optimal.
* **Confrontational:** Disruptive, high emotional spike.
* **Question:** Curiosity-driven, open loop.

Performance is measured via:
* **avg_watch_ratio (King Metric)**
* CTR / Impressions
* Engagement signals

## 🌀 Core Loop

`generate -> rank -> deploy -> measure -> bias -> regenerate`

## 📡 Status

* **Pipeline:** Operational
* **Egress:** Live (YouTube private upload)
* **Feedback Loop:** Active
* **Current Phase:** Data Collection / Calibration

## 🐺 Principle

The script does not matter if the first 5 seconds fail.

The system evolves toward what holds attention, not what sounds intelligent.

## ⌨️ Entry Points

```bash
python narrative-forge/run_full.py                # Execute the forge pipeline
python deploy_batch.py                            # Batch upload staged assets
python narrative-forge/scripts/feedback_ingest.py # Close the intelligence loop
python serve.py                                   # Boot API + worker locally
```

Windows launchers:

```bat
install.bat
start_web_shell.bat
```

## ✅ Prerequisites

- Windows environment with Python available in `PATH`
- `ffmpeg` available in `PATH` for packaging/transcode scripts
- `yt-dlp` support where required by harvest scripts
- Browser session/cookies available when using cookie-based extraction flows
- Local credential/token files for YouTube egress when using uploader scripts

## 🔒 Security and Artifact Boundary

- Do not commit tokens, cookies, OAuth credentials, or local key files.
- Do not assume hardcoded paths/credentials are safe defaults.
- Keep generated outputs and private source media outside tracked source whenever possible.
- See `SECURITY_NOTES.md` for operator safety baseline.

## ⚖️ Note

This is not a content generator. It is a **feedback-driven narrative evolution system.**
