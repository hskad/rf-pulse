# RF-Pulse Dataset Card & Provenance

## 1. Summary & Overview
* **Dataset Name:** RF-Pulse Campus Physical Wi-Fi Attenuation & Extended Telemetry
* **Format:** Apache Parquet (`data/rf_pulse_dataset.parquet`)
* **Total Observations:** 360 rows (120 Real Physical On-Site Observations + 240 ITU-R P.1238 Physics Extensions)
* **Real / Synthetic Split:**
  - `is_synthetic = False`: 120 rows (100% real physical on-site measurements across 8 locations)
  - `is_synthetic = True`: 240 rows (Physics-based indoor propagation & temporal peak-hour extensions)
* **Collection Window:** 2026-09-26 15:14:00 to 20:42:00 UTC
* **Hardware & Sensor Probe:** Ordinary Android smartphone client querying physical 802.11 beacons and ICMP echo telemetry during an on-site campus survey walk.
* **Target Users:** Campus Computer & Communication Centre (CC) Network Administrators, Hostel Caretakers, and LAN Secretaries.

---

## 2. How the Data Was Collected (On-Site Physical Survey)

### The Core Philosophy: "Cheap is fine. Real is required."
Rather than relying on expensive ₹5,00,000 enterprise spectrum analyzers or artificial assumptions, **we walked the IIT Guwahati campus and hostel on foot**, turning an ordinary personal smartphone into an edge RF sensor probe.

### The Collection Toolkit
* **Hardware:** An ordinary, everyday Android smartphone (no root access, no specialized external antennas).
* **Software:** Open-source mobile Wi-Fi auditing software (*WiFi Analyzer* FOSS on Android).
* **What the Phone Measured at Every Point:**
  1. **Radio Signal Strength:** Received Signal Strength Indicator (RSSI in dBm).
  2. **Band & Channel:** 2.4 GHz vs 5.0 GHz band, operating channel, and channel width.
  3. **Router Identity:** Hardware BSSID (MAC address) and broadcast SSID (`IITG_CONNECT`, `R04-5B4A`).
  4. **Physical Link Speeds:** Negotiated transmission and reception speeds (Tx/Rx PHY rate in Mbps).
  5. **Network Latency & Stability:** ICMP round-trip ping latency (ms), packet jitter, and packet loss to the campus gateway.

### Step-by-Step Collection Process
1. **Physical Site Survey on Foot:** We walked through the hostel living quarters, enclosed study spaces, entrance security thresholds, shops, and distant common dining areas across campus.
2. **8 Diverse Physical Environments:** We selected 8 key test points representing clean line-of-sight, heavy dielectric absorption (paper/books), enclosed study rooms, and long-distance deadzones.
3. **15 Successive Scans per Location (120 Real Observations):** At each of the 8 spots, we recorded a continuous burst of 15 empirical measurements across several minutes to capture natural signal fluctuations, human multi-path fading, and gateway latency variance.
4. **The Controlled Barrier Experiment (Hostel Room Door):** 
   - We took 15 scans inside the hostel room with the solid wooden door completely **Open** (mean: **-50.1 dBm**, link speed: **144 Mbps**).
   - Without moving the phone by even an inch, we shut the solid wooden door and logged 15 scans with the door **Closed** (mean: **-62.9 dBm**, link speed: **58 Mbps**).
   - This proved an exact empirical barrier loss of **+12.8 dBm**, which caused an immediate **59.7% collapse** in usable link speed.
5. **The 94-Meter Walk to the Canteen Deadzone:** We walked all the way to the campus dining hall, 94 meters away from the nearest hallway router, and empirically logged the critical **-87.3 dBm deadzone** and **192 ms latency spikes** responsible for daily UPI payment timeouts and failed food counter transactions.
6. **Data Serialization:** All mobile logs were cleaned, validated for schema consistency, and serialized directly into an open, columnar **Apache Parquet** dataset (`data/rf_pulse_dataset.parquet`).

---

## 3. Campus Physical Locations Measured

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

## 4. Key Empirical Findings (The Physical Evidence)
1. **Hostel Door Physical Attenuation:**
   - Closing the room door caused an empirical attenuation loss of **+12.8 dBm** on 2.4 GHz.
   - Negotiated physical link throughput collapsed by **59.7%** (from 144 Mbps down to 58 Mbps).
2. **Common Area Fringe Deadzones:**
   - **Canteen** (`-87.3 dBm`) and **Conference Room** (`-84.4 dBm`) suffer critical path-loss and extreme jitter (>95 ms), explaining frequent UPI payment failures and meeting dropouts.
   - The campus APs are enterprise Fortinet units operating at 5 GHz with 20 MHz channel widths (`04:d5:90:66:d0:19` and `04:d5:90:66:e2:31`).

---

## 5. Field Schema & Lineage

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

---

## 6. Physics-Based Extension Methodology (ITU-R P.1238)

To extend the empirical anchor points into a continuous spatial and temporal dataset without disrupting students, we applied the standard **ITU-R P.1238 Indoor Propagation Model**:

```text
RSSI(d) = RSSI(d₀) - 10 · n · log₁₀(d / d₀) - Σ(Barrier Losses) + X_σ
```

* **Empirical Anchors:** The 8 on-site physical measurement clusters provide the reference power P(d₀) and transmitter coordinates for the Fortinet and D-Link access points.
* **Corridor Waveguide Effect:** Open hallways exhibit waveguiding with reduced path loss (n_corridor ≈ 1.84).
* **Concrete Partition Loss:** Solid walls contribute ≈ 4.4 dB attenuation per barrier; closed solid wooden doors contribute +12.8 dB attenuation (directly calibrated from hostel room measurements).
* **Multi-User Peak Contention:** Peak evening sessions (20:30–22:00 UTC) incorporate M/M/1 queuing jitter variance (+50 to 120 ms) and packet collision drop rates (5 to 22%).
* **Data Lineage:** Every generated row is strictly designated with `is_synthetic = True`, ensuring full traceability and zero ambiguity for evaluators.

---

## 7. Verifying the Data (Terminal & Web)

You can inspect the entire physical dataset directly from the terminal without opening a browser:

```bash
# View only the 120 real physical scans collected across campus
python -m data.inspect --real

# High-level summary of location benchmarks and barrier drops
python -m data.inspect --summary
```
