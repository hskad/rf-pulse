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
* **Screen:** Show terminal running `python -m collector.probe --location Desk --door Open` and then `--door Closed`.
* **Narration:**
  > *"We didn't invent synthetic numbers. We collected empirical physical evidence right on our machine using native Windows OS wireless interface calls and ICMP echo probes.*
  > *Here, we sample our desk with the room door wide open: notice our RSSI is -64 dBm on Channel 13, negotiated at 144 Mbps.*
  > *Now, we close the heavy hostel door and sample again: look at the live telemetry—our RSSI drops immediately, physical link rate throttles, and latency spikes.*
  > *Every single observation is serialized directly into Apache Parquet with full metadata, timestamps, and explicit tags separating real physical edge measurements from our ITU-R indoor path-loss simulations."*

---

### [1:15 - 2:05] Part 3: The Live Web Dashboard & AI Decomposition
* **Screen:** Switch to browser running `http://localhost:8080`.
* **Narration:**
  > *"Here is the RF-Pulse dashboard. At the top, you can see our live AP connection and dataset provenance: 28 total observations, clearly showing our real physical points and synthetic extensions.*
  > *In the Physical Barrier Decomposition card, our model isolates the exact physical door attenuation: closing the door absorbed over 6 dBm of signal and caused a significant throughput drop.*
  > *Next, our AI Link Health classifier uses Random Forest to classify the link: notice it flags Channel 13 as CONGESTED because jitter exceeds 100 ms even when RSSI is moderate."*

---

### [2:05 - 2:45] Part 4: The Impact — Automated CC Dispatch Ticket
* **Screen:** Scroll down and highlight the Automated CC Remediation Ticket card on the dashboard.
* **Narration:**
  > *"Most hackathon projects end at a chart. RF-Pulse ends at an operational decision.*
  > *Our engine automatically compiles an official Computer & Communication Centre Remediation Ticket. It identifies the target BSSID, quantifies the door attenuation, and generates three specific engineering directives:*
  > *First: Reassign BSSID bc:22:28:c0:f1:b0 away from crowded Channel 13 to non-overlapping Channel 1 or 6.*
  > *Second: Adjust the 802.11k/v roaming threshold to permit graceful 2.4 GHz fallback when 5 GHz suffers heavy wall penetration loss.*
  > *With one click, the LAN secretary can copy this ticket and dispatch it directly to campus IT."*

---

### [2:45 - 3:00] Part 5: Conclusion & Inspection
* **Screen:** Show GitHub repository `https://github.com/hskad/rf-pulse` and the Parquet dataset card.
* **Narration:**
  > *"Our complete codebase, dataset schema card, and reproducible pipeline are available on our GitHub repository. RF-Pulse proves that with clean physical observations, an honest schema, and pragmatic AI, we can make campus infrastructure measurably better. Thank you."*
