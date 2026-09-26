"""
RF-Pulse: Physics-Based Indoor Propagation Simulator
Extends real-world baseline observations using ITU-R P.1238 indoor RF path-loss models.
Every generated row is explicitly tagged with `is_synthetic = True` to preserve data integrity.
"""

import argparse
import datetime
import os
import random
import uuid
import numpy as np
import pandas as pd


def generate_synthetic_rf_extensions(
    base_parquet="data/rf_pulse_dataset.parquet",
    output_parquet="data/rf_pulse_dataset.parquet",
    num_samples=30
):
    """
    Extends real empirical observations using Log-Distance Path Loss with Shadowing:
    PL(d) = PL(d0) + 10 * n * log10(d/d0) + WAF + X_sigma
    where WAF is Wall/Door Attenuation Factor.
    """
    if not os.path.exists(base_parquet):
        raise FileNotFoundError(f"Base dataset {base_parquet} does not exist.")

    real_df = pd.read_parquet(base_parquet)
    real_subset = real_df[real_df["is_synthetic"] == False]
    
    if real_subset.empty:
        baseline_rssi = -65.0
        baseline_tx = 144.0
        bssid = "bc:22:28:c0:f1:b0"
        ssid = "R04-F1B0"
        band = 2.4
        channel = 13
    else:
        baseline_rssi = float(real_subset["rssi_dbm"].mean())
        baseline_tx = float(real_subset["tx_rate_mbps"].mean()) if real_subset["tx_rate_mbps"].mean() else 144.0
        bssid = str(real_subset["bssid"].iloc[-1])
        ssid = str(real_subset["ssid"].iloc[-1])
        band = float(real_subset["band_ghz"].iloc[-1])
        channel = int(real_subset["channel"].iloc[-1])

    # Simulation scenarios (varying distance and physical wall barriers)
    scenarios = [
        {"location": "Adjacent_Room_1", "door": "Closed", "walls": 1, "dist_m": 8},
        {"location": "Adjacent_Room_2", "door": "Closed", "walls": 2, "dist_m": 14},
        {"location": "Corridor_Corner", "door": "Open", "walls": 0, "dist_m": 12},
        {"location": "Washroom_Deadzone", "door": "Closed", "walls": 2, "dist_m": 18}
    ]

    synthetic_records = []
    now = datetime.datetime.now(datetime.timezone.utc)

    # Path-loss exponent for residential/hostel concrete structure: n = 2.8
    n = 2.8
    # Wall attenuation factor per concrete wall: ~8 dBm
    waf_per_wall = 8.0
    # Door attenuation: ~5 dBm
    door_loss = 5.5

    for i in range(num_samples):
        sc = random.choice(scenarios)
        time_offset = datetime.timedelta(seconds=i * 10)
        
        # Free-space / log-distance path loss relative to baseline (d0 = 3m)
        dist_loss = 10 * n * np.log10(max(sc["dist_m"] / 3.0, 1.0))
        barrier_loss = (sc["walls"] * waf_per_wall) + (door_loss if sc["door"] == "Closed" else 0.0)
        shadow_fading = np.random.normal(0, 2.0)  # Log-normal shadowing (std = 2 dB)

        sim_rssi = round(baseline_rssi - dist_loss - barrier_loss + shadow_fading, 1)
        sim_rssi = max(min(sim_rssi, -30.0), -95.0)

        # Transmission rate drops non-linearly with lower RSSI (MCS index drop)
        if sim_rssi > -65:
            sim_tx = baseline_tx
        elif sim_rssi > -75:
            sim_tx = round(baseline_tx * 0.6, 1)
        elif sim_rssi > -85:
            sim_tx = round(baseline_tx * 0.25, 1)
        else:
            sim_tx = round(baseline_tx * 0.05, 1)

        # Latency & jitter increase as RSSI drops due to retransmissions
        base_rtt = 40.0 if sim_rssi > -70 else (90.0 if sim_rssi > -80 else 180.0)
        sim_rtt = round(base_rtt + np.random.exponential(20.0), 1)
        sim_jitter = round(np.random.exponential(15.0) + (40.0 if sim_rssi < -80 else 5.0), 1)
        sim_loss = 0.0 if sim_rssi > -80 else round(np.random.uniform(5.0, 30.0), 1)

        sim_signal_pct = int(max(0, min(100, (sim_rssi + 100) * 2)))

        record = {
            "timestamp": now + time_offset,
            "session_id": f"sim_{sc['location'].lower()[:10]}",
            "location_tag": sc["location"],
            "door_state": sc["door"],
            "is_synthetic": True,
            "ssid": ssid,
            "bssid": bssid,
            "band_ghz": band,
            "channel": channel,
            "radio_type": "802.11n",
            "signal_pct": sim_signal_pct,
            "rssi_dbm": sim_rssi,
            "tx_rate_mbps": sim_tx,
            "rx_rate_mbps": sim_tx,
            "ping_rtt_avg_ms": sim_rtt,
            "ping_jitter_ms": sim_jitter,
            "packet_loss_pct": sim_loss
        }
        synthetic_records.append(record)

    df_synth = pd.DataFrame(synthetic_records)
    df_combined = pd.concat([real_df, df_synth], ignore_index=True)
    df_combined.to_parquet(output_parquet, engine="pyarrow", index=False)

    print(f"[OK] Added {len(synthetic_records)} physics-based synthetic extensions.")
    print(f"[OK] Total dataset: {len(df_combined)} rows ({len(real_df)} real, {len(df_synth)} synthetic).")
    return len(df_combined)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RF-Pulse Indoor Path-Loss Simulator")
    parser.add_argument("--samples", type=int, default=25, help="Number of synthetic samples to generate")
    args = parser.parse_args()
    generate_synthetic_rf_extensions(num_samples=args.samples)
