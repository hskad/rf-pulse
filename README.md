# RF-Pulse: Physical Wi-Fi Deadzone & Link Degradation Auditor

> **Bring the Physical World to AI** — Granica × IIT Guwahati Hackathon (48 Hours)  
> *Transforming invisible Radio-Frequency (RF) physical wave attenuation into actionable IT infrastructure decisions.*

---

## 1. Problem & User

* **The Problem:** Campus residents frequently experience severe Wi-Fi dropouts during critical academic tasks (online tests, viva, coding competitions). Current network monitoring at the central Computer & Communication Centre (CC) only monitors aggregate throughput at the corridor Access Point (AP) level. They have zero granular visibility into how physical obstacles inside hostel rooms degrade real-world link quality.
* **The User:** **Campus Computer & Communication Centre (CC) Network Administrators** and the **Hostel LAN/Wi-Fi Committee**.
* **The Decision Question:** *Is student link failure caused by physical RF attenuation (concrete walls, metal almirahs, closed wooden doors) requiring physical AP relocation/repeater, or by spectral channel congestion requiring dynamic channel hopping?*

---

## 2. The Physical Workflow

Radio Frequency (RF) waves at 2.4 GHz and 5 GHz exhibit distinct physical wave propagation characteristics:
* **Physical Attenuation ($\Delta\text{RSSI}_{\text{physical}}$):** High-density materials (reinforced concrete: ~12–18 dB loss, closed solid wood doors: ~4–8 dB loss) absorb and scatter electromagnetic radiation. 5 GHz attenuates significantly faster than 2.4 GHz through solid barriers.
* **Temporal Interference & Congestion:** During peak evening hours (20:00–23:00), multi-user packet collisions and contention windows cause high packet jitter and loss even when raw signal strength (RSSI) appears adequate.

By treating the edge client (laptop) as an RF probe across specific physical room states (Door Open vs. Door Closed, Desk vs. Bed) and times of day, we capture the physical-to-digital reality.

---

## 3. Data Pipeline & Schema

All observations are serialized to the open **Apache Parquet** format with explicit metadata separating direct physical observations from model-inferred metrics.

### Parquet Schema Definition

| Field | Type | Nature | Description |
|---|---|---|---|
| `timestamp` | `datetime64[ns]` | Observed | ISO-8601 UTC timestamp of observation |
| `session_id` | `string` | Observed | Unique batch identifier |
| `location_tag` | `string` | Observed | Physical location (`Desk`, `Bed`, `Doorway`, `Window`) |
| `door_state` | `string` | Observed | Physical barrier state (`Open`, `Closed`) |
| `bssid` | `string` | Observed | Anonymized BSSID (MAC address of serving AP) |
| `ssid` | `string` | Observed | Network SSID |
| `band_ghz` | `float32` | Observed | Frequency band (`2.4` or `5.0`) |
| `channel` | `int32` | Observed | Operating Wi-Fi channel |
| `signal_pct` | `int32` | Observed | Windows raw signal percentage (0–100) |
| `rssi_dbm` | `float32` | Observed | Calculated RSSI: $\approx (\text{signal\_pct} / 2) - 100$ dBm |
| `tx_rate_mbps` | `float32` | Observed | Physical transmission link rate |
| `rx_rate_mbps` | `float32` | Observed | Physical reception link rate |
| `ping_rtt_avg_ms` | `float32` | Observed | Mean round-trip latency to gateway |
| `ping_jitter_ms` | `float32` | Observed | Latency variance / jitter |
| `packet_loss_pct` | `float32` | Observed | Packet loss percentage over sample window |
| `physical_loss_dbm`| `float32` | Inferred | Estimated material attenuation delta |
| `congestion_index` | `float32` | Inferred | Temporal interference score (0.0 to 1.0) |
| `link_health_state`| `string` | Inferred | Health classification (`OPTIMAL`, `ATTENUATED`, `CONGESTED`, `CRITICAL`) |

---

## 4. The AI Diagnostic Engine

1. **RF Material Attenuation Inversion:** Disentangles physical barrier loss from channel interference:
   $$\text{Degradation} = f(\Delta\text{RSSI}_{\text{barrier}}) + g(\text{Jitter}_{\text{spectral}})$$
2. **Predictive Link Health Classifier:** Supervised and anomaly models classifying link stability and forecasting connection drop risk.
3. **Smart Band & AP Recommender:** Recommends optimal band steering (switching to 2.4 GHz when 5 GHz suffers $>12\text{ dBm}$ wall attenuation, or switching channels when interference dominates).

---

## 5. The Action (What Changes for the User)

Instead of a passive dashboard, RF-Pulse outputs an **Automated CC Engineering Ticket**:
* Quantifies exact decibel loss induced by physical hostel infrastructure.
* Provides the CC team with actionable operational fixes: AP power adjustment, band-steering threshold updates, or auxiliary repeater installation points.

---

## 6. Quickstart

### Prerequisites
* Python 3.9+
* Windows OS (uses native `netsh wlan` interface probes)

### Installation
```bash
pip install -r requirements.txt
```

### Running the Probe
```bash
# Collect baseline data (e.g. at desk with door open)
python -m collector.probe --location Desk --door Open --samples 10

# Collect with physical barrier (door closed)
python -m collector.probe --location Desk --door Closed --samples 10
```

### Running the Diagnostics & Generating the CC Ticket
```bash
python -m models.diagnostics --data data/rf_pulse_dataset.parquet
```
