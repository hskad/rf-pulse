# RF-Pulse: Physical Wi-Fi Deadzone & Link Degradation Auditor

> **Bring the Physical World to AI** — Granica × IIT Guwahati Hackathon (48 Hours)  
> *Transforming invisible Radio-Frequency (RF) physical wave attenuation into actionable IT infrastructure decisions.*

---

## 1. Problem & User

* **The Problem:** Campus residents frequently experience severe Wi-Fi dropouts during critical academic tasks (online tests, viva, coding competitions). Current network monitoring at the central Computer & Communication Centre (CC) only monitors aggregate throughput at the corridor Access Point (AP) level. Central IT has zero granular visibility into how physical obstacles inside hostel rooms degrade real-world link quality.
* **The User:** **Campus Computer & Communication Centre (CC) Network Administrators** and the **Hostel LAN/Wi-Fi Committee**.
* **The Decision Question:** *Is student link failure caused by physical RF attenuation (concrete walls, metal fixtures, closed wooden doors) requiring physical AP relocation/repeater, or by spectral channel congestion requiring dynamic channel hopping?*

---

## 2. The Physical Workflow & Collection

Radio Frequency (RF) waves at 2.4 GHz and 5 GHz exhibit distinct physical wave propagation characteristics:
* **Physical Attenuation ($\Delta\text{RSSI}_{\text{physical}}$):** High-density materials (reinforced concrete: ~12–18 dB loss, closed solid wood doors: ~12.8 dB loss) absorb and scatter electromagnetic radiation. 5 GHz attenuates significantly faster than 2.4 GHz through solid barriers.
* **Long-Distance Fringe Deadzones:** Common areas located 75–95 meters away from corridor APs suffer severe path loss ($-84$ to $-87\text{ dBm}$) and ping jitter spikes (>100 ms), leading to dropped calls and UPI payment timeouts.

### The Dataset (`data/rf_pulse_dataset.parquet`)
- **120 Real Physical Observations:** Collected on-site across 8 campus environments using mobile Wi-Fi Analyzer telemetry:
  1. `Hostel_Room (Door Open)`: -50.1 dBm mean (2.4 GHz Ch 13)
  2. `Hostel_Room (Door Closed)`: -62.9 dBm mean $\rightarrow$ **+12.8 dBm empirical door drop, 59.7% PHY rate collapse**
  3. `Security Desk`: -49.9 dBm (1m from Fortinet AP)
  4. `Juice Centre`: -55.2 dBm (2m from Fortinet AP)
  5. `Reading Room`: -68.6 dBm (12m through door barrier)
  6. `Stationary Shop`: -68.9 dBm (12m from Fortinet AP)
  7. `Conference Room`: -84.4 dBm (76m distance $\rightarrow$ **Deadzone**)
  8. `Canteen`: -87.3 dBm (94m distance $\rightarrow$ **Critical Deadzone / UPI drop**)
- **240 Physics-Simulated Extensions:** Calibrated using the **ITU-R P.1238 Indoor Path-Loss Model**, modeling corridor waveguide propagation ($n=1.84$), concrete wall penetration ($4.4\text{ dB/wall}$), and peak evening traffic contention.
- **Total Dataset:** 360 observations with 100% explicit provenance (`is_synthetic` boolean flag).

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

1. **Physics-Informed Path-Loss Inversion ($R^2 = 0.935$):**
   - Fits the log-distance wave equation:
     $$\text{RSSI}(d) = \text{RSSI}_0 - 10 \cdot n \cdot \log_{10}(d) - \alpha_{\text{door}} \cdot I_{\text{door}} - \alpha_{\text{wall}} \cdot N_{\text{wall}}$$
   - Estimates empirical campus parameters:
     - Learned corridor waveguide exponent: $\hat{n} = 1.84$
     - Learned door attenuation: $\hat{\alpha}_{\text{door}} = 12.8\text{ dBm}$
     - Learned concrete wall attenuation: $\hat{\alpha}_{\text{wall}} = 4.4\text{ dBm}$
2. **Link Health Classification:**
   - Evaluates link stability across `OPTIMAL`, `ATTENUATED`, and `CRITICAL_DEADZONE`.
3. **Automated CC Dispatch Ticket:**
   - Translates findings into plain-English, actionable engineering directives for IT operations.

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

### Running the AI Diagnostic Engine
```bash
python -m models.diagnostics --data data/rf_pulse_dataset.parquet
```

### Launching the Web Interface
```bash
python -m web.server
```
Visit `http://localhost:8080` to inspect the live dashboard, view plain-English findings, and copy the CC dispatch ticket.
