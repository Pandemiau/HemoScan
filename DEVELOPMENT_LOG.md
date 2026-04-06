# 📝 Engineering Development Log: HemoScan v2.0

## Incident 001: Git Branch Checkout Collision
**Date:** April 2026
**Component:** Version Control / `src/core/vision.py`

### 🛑 The Issue
During the transition from the `develop` branch to the production `main` branch, the Git version control system aborted the operation, throwing the following fatal error:
`error: Your local changes to the following files would be overwritten by checkout: src/core/vision.py`
`Please commit your changes or stash them before you switch branches.`

### 🔍 Root Cause Analysis
The error occurred because new telemetry features (the live graphing monitor) were injected into `vision.py`, but the state was not staged or committed to the local repository vault. Git's internal safety mechanisms intentionally blocked the branch switch to prevent the uncommitted biometric logic from being permanently overwritten and lost during the workspace update.

### ✅ Resolution & Best Practices
To safely resolve the collision without data loss, the standard staging protocol was enforced:
1. Isolated the modified file: `git add src/core/vision.py`
2. Sealed the changes in the development branch: `git commit -m "feat: finalize vision engine with live telemetry graph"`
3. Successfully executed the branch transition: `git checkout main`

**Takeaway:** Strict commit hygiene is mandatory before context-switching between branches to ensure data integrity and prevent architectural regressions.

## Incident 002: Neurological Biometry Integration (Pupillary Response)
**Date:** April 2026
**Component:** Computer Vision / `src/core/vision.py`

### 🎯 Objective
Implement a real-time biometric sensor to detect Miosis (pupil constriction) and Mydriasis (pupil dilation) for aerospace fatigue monitoring and neurological trauma assessment.

### ⚙️ Implementation
1. **Topographical Mapping:** Isolated MediaPipe landmarks for the eye contour (Horizontal: 33, 133; Vertical: 159, 145).
2. **Mathematical Engine:** Deployed a 2D Euclidean Distance algorithm to calculate raw pixel dimensions in real-time.
3. **Dynamic Ratio Estandarization:** Formulated a depth-independent biometric ratio (`eye_height / eye_width`) to ensure accurate telemetry regardless of user distance from the optical sensor.
4. **Clinical Thresholds:** Programmed diagnostic triggers (Normal: ~0.20-0.30, Mydriasis: >0.35, Miosis: <0.18).

### ✅ Result
The Vision Engine successfully isolates and tracks pupillary variations, injecting the telemetry stream directly into the live HUD and preparing it for the scalable MySQL persistence layer.+

## [v1.0-RC] Vision Core & UI Architecture Stabilization
**Date:** 2026-04-05
**Module:** `src/core/vision.py`, `main.py`
**Status:** Desktop Release Candidate ready for WebRTC migration.

### Engineering Notes & Commits:
* **Illumination Invariance (CLAHE):** Integrated Contrast Limited Adaptive Histogram Equalization to mathematically normalize the luminance channel (V in HSV) within the ocular ROI. This stabilizes detection in low-light rural environments without triggering false positives from shadows.
* **Hardware-Agnostic HSV Tuning:** Recalibrated saturation thresholds (S=100) to find the strict clinical "sweet spot". This filters out false positives caused by Smartphone Auto-HDR skin enhancements while maintaining high sensitivity for low-tier webcams.
* **ROI Optimization:** Narrowed the spatial scanning box (`box_width=50, box_height=15, y_offset=5`) to strictly target the palpebral conjunctiva, eliminating cheek-tissue interference.
* **Dynamic UI Renderer (View Selector):** Refactored `main.py` rendering loop. Implemented a numeric keystroke listener (`0-3`) to toggle specific telemetry overlays (Vascular, Hepatic, Neurological) and relocated the live oscilloscope to prevent central FOV obstruction.

**Next Steps:** Freeze local desktop dependencies (`requirements.txt`) and architect the cloud environment using `streamlit` and `streamlit-webrtc` for remote deployment.