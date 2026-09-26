# RF-Pulse: 3-Minute Demo Video Script (Second-by-Second)

> **Total Time:** 180 seconds (3:00)  
> **Judges:** Granica Engineers & External Panel  
> **Key Goal:** Prove real physical data collection, inspectable Parquet schema, AI diagnostic logic, and actionable CC impact.

---

### [0:00 - 0:35] Part 1: The Problem & The Named User
* **Screen:** Show Slide 1 or start in front of the laptop with the hostel room door visible.
* **Narration:**
  > *"Hello judges. Across campus hostels, students frequently face dropped Wi-Fi connections during online exams and interviews. Today, the Computer & Communication Centre (CC) only monitors aggregate throughput at corridor Access Points. They cannot see through hostel walls.*
  > *They don't know if a connection is failing due to physical electromagnetic wave absorption from closed doors and concrete walls, or spectral congestion from 40 devices on the same channel.*
  > *This is RF-Pulse: bringing the physical reality of radio-frequency propagation to AI, turning edge laptops into physical RF probes."*

---

### [0:35 - 1:15] Part 2: Physical Workflow & Real Data Collection
* **Screen:** Show terminal or dataset view of the 8 measured locations.
* **Narration:**
  > *"We didn't invent numbers. We conducted an on-site physical survey across 8 campus hostel locations using a mobile Wi-Fi Analyzer, recording 120 real physical measurements across our room, Reading Room, Canteen, Security Desk, Juice Centre, and Conference Room.*
  > *Look at our room measurements: with the door wide open, signal is -50 dBm. When the door is closed, it drops to -63 dBm—an empirical loss of +12.8 dBm that collapses physical throughput by nearly 60%.*
  > *Every single observation is serialized directly into Apache Parquet with full timestamps, BSSID hardware addresses, and frequency telemetry."*

---

### [1:15 - 2:05] Part 3: The Live Web Dashboard & Physical Decomposition
* **Screen:** Switch to browser running `http://localhost:8080`.
* **Narration:**
  > *"Here is the RF-Pulse dashboard, designed around Granica's minimalist engineering philosophy: high-contrast, uncluttered, and data-first.*
  > *At the top, the status bar shows our 120 real empirical observations across our campus locations.*
  > *In the 3-column metric grid, our engine isolates the core physics: our signal strength, the +12.8 dBm empirical absorption across the closed door barrier, and the latency variance.*
  > *Below that is our live Parquet stream, where any judge can inspect the 120 rows and 8 audited physical environments."*

---

### [2:05 - 2:45] Part 4: The Impact — Automated CC Dispatch Ticket
* **Screen:** Scroll down and highlight the Automated CC Remediation Ticket card on the dashboard.
* **Narration:**
  > *"Most hackathon projects end at a chart. RF-Pulse ends at an operational decision.*
  > *Our engine automatically compiles an official Computer & Communication Centre Remediation Ticket.*
  > *It flags that the Canteen and Conference Room are 75 to 95 meters away from the nearest Fortinet APs, sitting at -85 to -87 dBm with over 100 ms of jitter—identifying the exact physical reason UPI payments and video calls fail there.*
  > *It generates targeted engineering directives: auxiliary AP brackets for the Canteen and Conference Room, and adjusted 802.11k/v roaming thresholds for heavy-door hostel blocks.*
  > *With one click, the LAN secretary can copy this ticket and dispatch it directly to campus IT."*

---

### [2:45 - 3:00] Part 5: Conclusion & Inspection
* **Screen:** Show GitHub repository `https://github.com/hskad/rf-pulse` and the Parquet dataset card.
* **Narration:**
  > *"Our complete codebase, dataset schema card, and reproducible pipeline are available on our GitHub repository. RF-Pulse proves that with clean physical observations, an honest schema, and pragmatic AI, we can make campus infrastructure measurably better. Thank you."*
