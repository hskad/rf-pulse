# RF-Pulse: Physical Wi-Fi Deadzone & Link Degradation Auditor

## 1. Problem & User

* **The Problem:** Campus residents frequently experience severe Wi-Fi dropouts during critical academic tasks (online tests, viva, coding competitions). Current network monitoring at the central Computer & Communication Centre (CC) only monitors aggregate throughput at the corridor Access Point (AP) level. Central IT has zero granular visibility into how physical obstacles inside hostel rooms degrade real-world link quality.
* **The User:** **Campus Computer & Communication Centre (CC) Network Administrators** and the **Hostel LAN/Wi-Fi Committee**.
* **The Decision Question:** *Is student link failure caused by physical RF attenuation (concrete walls, metal fixtures, closed wooden doors) requiring physical AP relocation/repeater, or by spectral channel congestion requiring dynamic channel hopping?*

---

## 2. Physical Data Collection & Telemetry Lake

### The On-Site Collection Journey (Walking Campus & Hostel)
The hackathon problem statement emphasizes: *"A clever proxy can beat expensive equipment. Cheap is fine. Real is required."* Rather than relying on simulated assumptions or inaccessible ₹5,00,000 lab spectrum analyzers, **we walked the IIT Guwahati campus and hostel on foot**, using an everyday Android smartphone as an edge RF sensor probe.

* **Open-Source Tooling on the Phone:** We deployed open-source mobile Wi-Fi auditing software (*WiFi Analyzer* / open network telemetry utilities on Android) to passively listen to raw 802.11 beacon frames, hardware BSSIDs, frequency bands (2.4 GHz vs 5.0 GHz), operating channels, and negotiated physical link speeds (Tx/Rx PHY rate), coupled with gateway ICMP echo latency measurements.
* **120 Real Ground-Truth Physical Scans:** We conducted an on-site physical site survey across **8 distinct campus environments**, logging bursts of 15 successive empirical measurements at each location to capture real signal fluctuations, multi-path fading, and physical obstruction effects:
  1. `Hostel_Room (Door Open)`: Line-of-sight to corridor router (**-50.1 dBm**, 144 Mbps link rate).
  2. `Hostel_Room (Door Closed)`: Same physical position with standard solid wooden door shut → **+12.8 dBm empirical signal loss, collapsing speed by 59.7% down to 58 Mbps**.
  3. `Security Desk`: 1 meter line-of-sight from enterprise Fortinet AP (**-49.9 dBm**, 400 Mbps).
  4. `Juice Centre`: Outdoor boundary threshold 2 meters away (**-55.2 dBm**, 300 Mbps).
  5. `Reading Room`: Enclosed study space behind interior partitions (**-68.6 dBm**, 173 Mbps).
  6. `Stationary Shop`: High paper stack dielectric absorption area (**-68.9 dBm**, 173 Mbps).
  7. `Conference Room`: Shielded space with heavy acoustic panels 76m away (**-84.4 dBm**, 54 Mbps deadzone).
  8. `Canteen`: Dining hall 94m away from the nearest AP (**-87.3 dBm**, 36 Mbps, 192 ms RTT latency) → **Critical Deadzone explaining widespread UPI payment timeouts**.

### The Parquet Telemetry Lake (`data/rf_pulse_dataset.parquet`)
All mobile telemetry logs were structured and serialized into a lightweight, columnar **Apache Parquet** dataset (19.7 KB, 17 strictly typed schema columns) with 100% verified lineage:
* **120 Real Physical Observations (`is_synthetic = False`):** Genuine ground-truth measurements collected on-site by walking the campus.
* **240 Calibrated ITU-R Extensions (`is_synthetic = True`):** Calibrated using the international **ITU-R P.1238 Indoor Path-Loss Model**, extending the empirical anchors to simulate peak dinner-rush contention and adjacent concrete walls.
* **Total Dataset:** 360 observations with zero schema drift. Every single row carries an explicit boolean flag so judges and engineers can instantly isolate real vs. extended data.

### Inspecting the Telemetry (TUI & Web)
You can verify the dataset lineage and empirical findings without a browser using the built-in terminal inspector:
```bash
# Inspect only the 120 real physical scans collected on campus
python -m data.inspect --real

# High-level summary of physical barrier drops and location benchmarks
python -m data.inspect --summary
```
Or interactively filter between **All (360)**, **Real Physical (120)**, and **Simulated (240)** on the live web dashboard.

---

## 3. Parquet Schema Definition

All observations are serialized to open **Apache Parquet** format:

| Field | Type | Nature | Description |
|---|---|---|---|
| `timestamp` | `datetime64[ns]` | Observed | ISO-8601 UTC timestamp of observation |
| `session_id` | `string` | Observed | Batch session identifier |
| `location_tag` | `string` | Observed | Physical location (`Hostel_Room`, `Reading_Room`, `Security_Desk`, `Juice_Centre`, `Canteen`, etc.) |
| `door_state` | `string` | Observed | Physical barrier state (`Open`, `Closed`) |
| `is_synthetic` | `bool` | Provenance | `False` for real on-site measurements, `True` for physics-simulated extensions |
| `bssid` | `string` | Observed | Hardware MAC address of serving AP |
| `ssid` | `string` | Observed | Network SSID (`IITG_CONNECT`, `R04-5B4A`) |
| `band_ghz` | `float32` | Observed | Frequency band (`2.4` or `5.0`) |
| `channel` | `int32` | Observed | Operating Wi-Fi channel |
| `rssi_dbm` | `float32` | Observed | Received Signal Strength Indicator in decibel-milliwatts |
| `tx_rate_mbps` | `float32` | Observed | Physical transmission link rate |
| `rx_rate_mbps` | `float32` | Observed | Physical reception link rate |
| `ping_rtt_avg_ms` | `float32` | Observed | Mean round-trip latency to gateway |
| `ping_jitter_ms` | `float32` | Observed | Latency variance / jitter |
| `packet_loss_pct` | `float32` | Observed | Packet loss percentage over sample window |

---

## 4. The AI Diagnostic Engine (`models/diagnostics.py`)

### 1. Physics-Informed Path-Loss Inversion (R² = 0.935)
Rather than relying on opaque black-box deep learning, RF-Pulse fits an empirical log-distance wave propagation model to isolate physical obstacle absorption from spatial distance loss:

```text
RSSI(d) = RSSI₀ - 10 · n · log₁₀(d) - α_door · I_door - α_wall · N_wall
```

**Learned Campus Physical Parameters:**
* **Corridor Waveguide Exponent (n̂):** `1.84` (radio waves funnel efficiently down open hallways)
* **Door Barrier Attenuation (α̂_door):** `+12.8 dBm` (19.2× energy reduction through solid wood door)
* **Concrete Partition Loss (α̂_wall):** `+4.4 dBm` per interior partition wall

### 2. Link Health Classification
A lightweight classifier categorizes real-time connection stability into three distinct physical operating states:
* `OPTIMAL`: RSSI ≥ -65 dBm, PHY rate ≥ 50 Mbps, jitter < 20 ms (clean line-of-sight).
* `ATTENUATED`: RSSI between -65 dBm and -80 dBm (signal degraded by concrete/doors, high risk of dropouts).
* `CRITICAL_DEADZONE`: RSSI < -80 dBm, ping latency > 100 ms (packet loss cascade, payment timeouts).

### 3. Automated CC Dispatch Ticket
Translates complex RF wave telemetry directly into plain-English, actionable engineering directives for campus IT operations.

---

## 5. The Action (What Changes for the User)

Instead of a passive dashboard with raw charts, RF-Pulse outputs an **Automated CC Remediation Ticket**:
1. **Corridor AP Re-positioning:** Shift hallway AP bracket 1.5–2m closer to room clusters to compensate for closed-door loss (+12.8 dBm).
2. **Canteen Auxiliary AP:** Install a dedicated ceiling access point in the Canteen to eliminate the 94-meter coverage gap and prevent UPI timeouts.
3. **Smart Band Steering:** Lower roaming thresholds to allow smooth fallback to 2.4 GHz when doors are shut.

---

## 6. Quickstart

### Prerequisites
* Python 3.9+
* Recommended: Virtual environment (`venv`)

### Installation
```bash
pip install -r requirements.txt
```

### Inspecting the Dataset (Terminal UI)
```bash
# View the 120 empirical physical scans collected on-site
python -m data.inspect --real
```

### Running the AI Diagnostic Engine
```bash
python -m models.diagnostics --data data/rf_pulse_dataset.parquet
```

### Launching the Web Interface
```bash
python -m web.server
```
Visit `http://localhost:8080` to inspect the live dashboard, view plain-English findings, and copy the CC dispatch ticket.
