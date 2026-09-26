# RF-Pulse Dataset Card & Provenance

## 1. Summary & Overview
* **Dataset Name:** RF-Pulse Campus Physical Wi-Fi Attenuation & Common Area Telemetry
* **Format:** Apache Parquet (`data/rf_pulse_dataset.parquet`)
* **Total Observations:** 120 rows across 8 distinct campus hostel environments
* **Collection Window:** 2026-09-26 15:14:00 to 15:32:28 UTC
* **Hardware & Sensor Probe:** Android WiFi Analyzer by olgor.com on smartphone client querying physical 802.11 beacons and ICMP echo telemetry.
* **Target Users:** Campus Computer & Communication Centre (CC) Network Administrators, Hostel Caretakers, and LAN Secretaries.

---

## 2. Campus Physical Locations Measured

| Location | Physical Barrier / Environment | Target AP SSID | Frequency Band | Serving AP BSSID | Mean RSSI | Jitter |
|---|---|---|---|---|---|---|
| **Hostel Room (Door Open)** | Direct Line-of-Sight (LoS) | `R04-5B4A` | 2.4 GHz (Ch 13) | `a4:2a:95:29:5b:4a` | **-50.1 dBm** | 8.5 ms |
| **Hostel Room (Door Closed)** | Solid Wooden Door Barrier | `R04-5B4A` | 2.4 GHz (Ch 13) | `a4:2a:95:29:5b:4a` | **-62.9 dBm** | 15.7 ms |
| **Security Desk** | Entrance Gate Threshold (1m from AP) | `IITG_CONNECT` | 5.0 GHz (Ch 132) | `04:d5:90:66:d0:19` | **-49.9 dBm** | 9.5 ms |
| **Juice Centre** | Courtyard / Outdoor Boundary (2m LoS) | `IITG_CONNECT` | 5.0 GHz (Ch 116) | `04:d5:90:66:e2:31` | **-55.2 dBm** | 13.6 ms |
| **Reading Room** | High-Density Enclosed Study Space | `IITG_CONNECT` | 5.0 GHz (Ch 116) | `04:d5:90:66:e2:31` | **-68.6 dBm** | 33.8 ms |
| **Stationary Shop** | High Paper Stack Dielectric Absorption | `IITG_CONNECT` | 5.0 GHz (Ch 132) | `04:d5:90:66:d0:19` | **-68.9 dBm** | 31.2 ms |
| **Conference Room** | Shielded Room / Heavy Acoustic Panels (76m) | `IITG_CONNECT` | 5.0 GHz (Ch 116) | `04:d5:90:66:e2:31` | **-84.4 dBm** | 97.6 ms |
| **Canteen** | Industrial Appliances & Multi-Path Fading (94m) | `IITG_CONNECT` | 5.0 GHz (Ch 132) | `04:d5:90:66:d0:19` | **-87.3 dBm** | 109.5 ms |

---

## 3. Key Empirical Findings (The Physical Evidence)
1. **Hostel Door Physical Attenuation:**
   - Closing the room door caused an empirical attenuation loss of **+12.8 dBm** on 2.4 GHz.
   - Negotiated physical link throughput collapsed by **59.7%** (from 144 Mbps down to 58 Mbps).
2. **Common Area Fringe Deadzones:**
   - **Canteen** (`-87.3 dBm`) and **Conference Room** (`-84.4 dBm`) suffer critical path-loss and extreme jitter ($>95\text{ ms}$), explaining frequent UPI payment failures and meeting dropouts.
   - The campus APs are enterprise Fortinet units operating at 5 GHz with 20 MHz channel widths (`04:d5:90:66:d0:19` and `04:d5:90:66:e2:31`).

---

## 4. Field Schema & Lineage

| Column | Type | Origin | Description |
|---|---|---|---|
| `timestamp` | `datetime64[ns, UTC]` | Observed | Hardware timestamp of observation |
| `session_id` | `string` | Observed | Batch session identifier (e.g. `burst_hostel_r`) |
| `location_tag` | `string` | Ground Truth | Physical location within hostel complex |
| `door_state` | `string` | Ground Truth | Physical barrier state (`Open`, `Closed`) |
| `is_synthetic` | `boolean` | Lineage | `False` for empirical physical readings; `True` if extended |
| `ssid` | `string` | Observed | Broadcast network identifier (`IITG_CONNECT`, `R04-5B4A`) |
| `bssid` | `string` | Observed | Hardware MAC of serving AP |
| `band_ghz` | `float64` | Observed | Frequency band (`2.4` or `5.0` GHz) |
| `channel` | `int64` | Observed | Wi-Fi operational channel |
| `radio_type` | `string` | Observed | 802.11 physical standard (`802.11n`, `802.11ac`) |
| `signal_pct` | `int64` | Observed | Signal quality index percentage (0–100%) |
| `rssi_dbm` | `float64` | Observed | Received Signal Strength Indicator (dBm) |
| `tx_rate_mbps` | `float64` | Observed | Negotiated transmission link rate (Mbps) |
| `rx_rate_mbps` | `float64` | Observed | Negotiated reception link rate (Mbps) |
| `ping_rtt_avg_ms` | `float64` | Observed | Average round-trip latency to campus gateway |
| `ping_jitter_ms` | `float64` | Observed | Latency variance / jitter (ms) |
| `packet_loss_pct` | `float64` | Observed | Packet loss percentage over sample burst |
