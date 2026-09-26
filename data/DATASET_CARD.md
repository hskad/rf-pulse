# RF-Pulse Dataset Card & Provenance

## 1. Summary & Overview
* **Name:** RF-Pulse Physical Wi-Fi Attenuation & Link Telemetry Dataset
* **Format:** Apache Parquet (`data/rf_pulse_dataset.parquet`)
* **Target Audience:** Campus IT / Computer & Communication Centre (CC) Network Administrators, Systems Researchers.
* **Collection Method:** Direct edge OS system calls via native Windows `netsh wlan` wireless interface statistics and ICMP ping probes.

---

## 2. Field Schema & Lineage

| Column | Type | Origin | Description |
|---|---|---|---|
| `timestamp` | `datetime64[ns, UTC]` | Observed | Direct UTC hardware timestamp |
| `session_id` | `string` | Observed | Batch session identifier |
| `location_tag` | `string` | Ground Truth | Physical location within indoor space (`Desk`, `Bed`, `Doorway`, `Window`) |
| `door_state` | `string` | Ground Truth | State of physical barrier (`Open`, `Closed`) |
| `is_synthetic` | `boolean` | Metadata | `False` for real edge measurements; `True` if extended synthetically |
| `ssid` | `string` | Observed | Broadcast network identifier |
| `bssid` | `string` | Observed | Hardware MAC address of the serving Access Point |
| `band_ghz` | `float64` | Observed | Frequency band (`2.4` or `5.0` GHz) |
| `channel` | `int64` | Observed | Wi-Fi operational channel |
| `radio_type` | `string` | Observed | 802.11 physical layer standard (e.g., `802.11n`, `802.11ac`, `802.11ax`) |
| `signal_pct` | `int64` | Observed | Raw OS link signal quality percentage (0–100%) |
| `rssi_dbm` | `float64` | Observed | Direct Received Signal Strength Indicator in decibel-milliwatts (dBm) |
| `tx_rate_mbps` | `float64` | Observed | Negotiated transmission link rate (Mbps) |
| `rx_rate_mbps` | `float64` | Observed | Negotiated reception link rate (Mbps) |
| `ping_rtt_avg_ms` | `float64` | Observed | Average round-trip latency over 4 ICMP echo packets |
| `ping_jitter_ms` | `float64` | Observed | Latency variance ($\text{RTT}_{\max} - \text{RTT}_{\min}$) |
| `packet_loss_pct` | `float64` | Observed | Percentage of dropped packets in sample window |

---

## 3. Physical Workflow & Collection Cadence
* **Cadence:** Sampled at 1–3 second intervals in continuous batches per physical scenario.
* **Physical Conditions Tested:**
  1. **Line-of-Sight (LoS):** Desk with room door Open.
  2. **Non-Line-of-Sight (NLoS - Barrier):** Desk with room door Closed (physical solid barrier attenuation).
  3. **Multi-path / Deadzone:** Room corners, behind metallic furniture / wardrobe.
* **Traceability & Integrity:**
  Zero mock or simulated data is passed off as real. Any synthetic physics extensions are strictly tagged with `is_synthetic = True`.
