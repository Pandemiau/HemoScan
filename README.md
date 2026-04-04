#  HemoScan v2.0: Biometric Telemetry & Optical Analysis System

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Architecture](https://img.shields.io/badge/architecture-MVC-success.svg)
![Security](https://img.shields.io/badge/security-SHA--256-red.svg)

##  Project Overview
**HemoScan v2.0** is a real-time, non-invasive optical telemetry system designed for early-stage medical anomaly detection. Conceived with **Aerospace Engineering and isolated-habitat monitoring** in mind, the system uses standard RGB camera feeds (simulating low-bandwidth remote sensors) to extract and analyze human biometric markers without requiring physical blood samples.

##  The "Why": Motivation & Vision

While traditional blood work requires established clinical infrastructure, needles, and time, **HemoScan** was born from a deeply personal necessity. In developing regions like my home country of Guatemala, access to basic healthcare is often hindered by severe geographic and financial barriers. Watching my grandparents endure hours of painful travel to urban centers just to afford simple, yet expensive, diagnostic tests highlighted a systemic failure. Vulnerable populations need accessible, early-warning health systems.

HemoScan was engineered to democratize medical diagnostics. By transforming a standard camera into a non-invasive biometric sensor, we bypass the need for physical laboratories. While currently tuned for Anemia and Jaundice detection, the system's modular architecture is designed to continuously scale, integrating new disease-detection models in the future.

Furthermore, as my focus expands toward **Aerospace Engineering**, this project serves as a foundational prototype for **Space Medicine and Telemetry**. The parallels are clear: in isolated environments—whether a remote rural village or a deep-space habitat—traditional clinical laboratories are simply unviable. Non-invasive, camera-based diagnostic algorithms like HemoScan represent the future of autonomous crew health monitoring.

The engine currently processes two primary telemetry streams:
1.  **Vascular Module:** Conjunctival Pallor analysis for early Anemia detection.
2.  **Hepatic Module:** Scleral Icterus analysis for Jaundice detection.

##  System Architecture (Clean MVC)
The codebase has been refactored from a monolithic script into an industrial-grade, object-oriented architecture to ensure scalability, fault tolerance, and separation of concerns.

* `src/core/vision.py`: **The Flight Computer.** Handles MediaPipe Face Mesh neural networks, Numpy vectorized color space processing (HSV), dynamic lighting filters, and moving-average stabilizers.
* `src/core/security.py`: **Data Integrity.** Implements SHA-256 cryptographic hashing acting as a digital "black box" to guarantee medical data immutability against transmission corruption.
* `src/database/db_manager.py`: **Persistence Layer.** Isolated MySQL connector for secure biometric record keeping.
* `src/ui/dashboard.py`: **Mission Control.** Handles the CustomTkinter GUI, asynchronous background tasks (Voice Synthesis & SMTP Email protocols), and hardware keyboard interrupts.
* `main.py`: **The Orchestrator.** Connects the UI, starts the optical sensor, and runs the main telemetry loop.

##  Core Technical Features
* **PIP (Picture-in-Picture) Minimap:** Real-time isolated ROI extraction for clinical debugging.
* **Dynamic White-Balancing:** Keyboard interrupts allow manual threshold calibration to adapt to fluctuating lighting conditions.
* **Fault-Tolerant Asynchronous IO:** Email generation, PDF creation, and Voice Synthesis run on detached background threads (`threading`) to prevent UI freezing or frame dropping.
* **Live Telemetry HUD:** Real-time plotting of biometric stability arrays directly on the OpenCV video feed.

##  Installation & Deployment

1. Clone the repository and navigate to the root directory.

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt

3. Ensure a local MySQL instance (e.g., XAMPP) is running with a database named hemoscan_db.

4. Ignite the main sequence:
   ```bash
   python main.py

5. Note on Security: SMTP credentials for background email notifications have been explicitly decoupled from the source code for repository security. To test the email functionality, supply local .env credentials in the SystemNotifier class.

Designed and engineered for advanced structural and system implementations.