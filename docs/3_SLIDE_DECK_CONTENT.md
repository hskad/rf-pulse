# RF-Pulse: 3-Slide Presentation Deck Content
*Granica × IIT Guwahati Hackathon · 48 Hours*

---

## Slide 1: The Problem, The User & The Question

### Title: The Invisible Wall: Decoupling Physical RF Loss from Campus Wi-Fi Failure
* **The User:** **Campus Computer & Communication Centre (CC) Network Operations** & **Hostel LAN/Wi-Fi Committee**.
* **The Real Problem:**
  Students across campus hostels report sudden link freezes and dropped connections during high-stakes exams, interviews, and remote lectures. Central IT network monitoring only observes aggregate throughput on corridor Access Points (APs) and cannot see inside the room. They have zero visibility into whether connection drops are caused by **physical structural obstacles** or **temporal network congestion**.
* **The Core Question:**
  *How much physical RF attenuation do hostel barriers (closed solid doors, concrete walls) inflict on 2.4 GHz vs 5 GHz signals, and how can edge client telemetry automate targeted AP power, channel, and band-steering remediations for IT operations?*

---

## Slide 2: The Physical Workflow, Collection & Solution

### Title: Edge Probing to Parquet: Transforming Wave Physics into Structured Evidence
* **Physical Workflow:**
  High-frequency electromagnetic waves (2.4 GHz and 5 GHz) attenuate exponentially when penetrating concrete walls, metal fixtures, and solid hostel doors. In parallel, common area fringe distances create packet retransmission cascades and latency jitter.
* **Collection Method (On-Site Mobile RF Survey):**
  - **The Probe:** On-site smartphone client using WiFi Analyzer querying physical 802.11 beacons and network latency telemetry.
  - **Physical Environments Audited (8 Locations):** Hostel Room (Door Open vs. Closed), Reading Room, Security Desk, Juice Centre, Canteen, Stationary Shop, and Conference Room.
  - **The Dataset:** 120 empirical physical observations (15 successive scans sampled per location) serialized to open **Apache Parquet** (`data/rf_pulse_dataset.parquet`).
* **The Solution Architecture:**
  - **RF Attenuation Inversion Engine:** Quantifies exact physical barrier absorption ($\Delta\text{RSSI}_{\text{door}} = +12.8\text{ dBm}$) and physical PHY rate drops.
  - **Link Health Classifier:** Machine learning model classifying link states (`OPTIMAL`, `ATTENUATED`, `CONGESTED`, `CRITICAL_RISK`).

---

## Slide 3: The Result, User Impact & Live Demo

### Title: From Physical Wave Loss to an Automated CC Remediation Ticket
* **What We Discovered (The Empirical Evidence):**
  - **Closed Door Absorption:** Closing the hostel room door causes an empirical drop of **+12.8 dBm** on 2.4 GHz (from -50 dBm to -63 dBm), triggering a **59.7% collapse** in physical link rate (144 Mbps down to 58 Mbps).
  - **Common Area Deadzones:** Canteen (**-87.3 dBm**, 109.5 ms jitter) and Conference Room (**-84.4 dBm**, 97.6 ms jitter) suffer critical fringe path-loss from Fortinet APs 75–95m away, explaining widespread UPI payment and video call failures.
* **What Changes for the User (Actionable Impact):**
  Instead of passive graphs, RF-Pulse outputs an **Automated CC Network Dispatch Ticket**:
  1. Recommends auxiliary AP installation / repeater bracket targeting Canteen and Conference Room deadzones.
  2. Adjusts 802.11k/v roaming thresholds to trigger 2.4 GHz fallback when closed doors inflict >12 dBm attenuation.
  3. Reallocates congested AP channels away from overlapping frequencies.
* **Project Artifacts & Links:**
  - **Live Code Repository:** `https://github.com/hskad/rf-pulse`
  - **Dataset:** `data/rf_pulse_dataset.parquet` (Complete schema card & provenance included)
  - **Live Interactive Dashboard:** `http://localhost:8080`
