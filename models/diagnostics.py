"""
RF-Pulse: AI Diagnostic & Recommendation Engine
Disentangles physical RF barrier attenuation from spectral congestion,
classifies link health, and generates actionable IT dispatch recommendations.
"""

import argparse
import os
import numpy as np
import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

console = Console()


def load_telemetry(parquet_path="data/rf_pulse_dataset.parquet"):
    """Loads and validates parquet telemetry data."""
    if not os.path.exists(parquet_path):
        raise FileNotFoundError(f"Dataset not found at {parquet_path}. Run collector first.")
    df = pd.read_parquet(parquet_path)
    return df


def compute_physical_attenuation(df):
    """
    Decomposes physical barrier loss by comparing open vs closed door states
    for the same physical location tag.
    """
    summary = {}
    locations = df["location_tag"].unique()

    for loc in locations:
        loc_df = df[df["location_tag"] == loc]
        open_df = loc_df[loc_df["door_state"] == "Open"]
        closed_df = loc_df[loc_df["door_state"] == "Closed"]

        avg_open_rssi = open_df["rssi_dbm"].mean() if not open_df.empty else None
        avg_closed_rssi = closed_df["rssi_dbm"].mean() if not closed_df.empty else None

        delta_dbm = None
        if avg_open_rssi is not None and avg_closed_rssi is not None:
            # Physical loss = Open RSSI - Closed RSSI (positive value means signal dropped)
            delta_dbm = round(avg_open_rssi - avg_closed_rssi, 2)

        avg_open_tx = open_df["tx_rate_mbps"].mean() if not open_df.empty else None
        avg_closed_tx = closed_df["tx_rate_mbps"].mean() if not closed_df.empty else None
        tx_drop_pct = None
        if avg_open_tx and avg_closed_tx and avg_open_tx > 0:
            tx_drop_pct = round(((avg_open_tx - avg_closed_tx) / avg_open_tx) * 100, 1)

        summary[loc] = {
            "avg_open_rssi": avg_open_rssi,
            "avg_closed_rssi": avg_closed_rssi,
            "physical_delta_dbm": delta_dbm,
            "avg_open_tx": avg_open_tx,
            "avg_closed_tx": avg_closed_tx,
            "tx_drop_pct": tx_drop_pct,
            "sample_count": len(loc_df)
        }
    return summary


def train_link_health_classifier(df):
    """
    Trains a model to categorize link health into operational states:
    - OPTIMAL: High RSSI, low latency, low jitter
    - ATTENUATED: Low RSSI due to physical obstacle, but moderate jitter
    - CONGESTED: Decent RSSI, but high jitter and latency variance
    - CRITICAL: Severe packet drop or extreme attenuation
    """
    # Feature engineering for health state
    features = ["rssi_dbm", "tx_rate_mbps", "ping_rtt_avg_ms", "ping_jitter_ms", "packet_loss_pct"]
    
    # Fill NAs
    clean_df = df.copy()
    for col in features:
        if col in clean_df.columns:
            clean_df[col] = clean_df[col].fillna(clean_df[col].median() if not clean_df[col].dropna().empty else 0)

    # Rule-based ground truth generator for initial supervision
    def label_sample(row):
        loss = row.get("packet_loss_pct", 0)
        rssi = row.get("rssi_dbm", -70)
        jitter = row.get("ping_jitter_ms", 20)
        rtt = row.get("ping_rtt_avg_ms", 50)

        if loss > 15 or rssi < -85:
            return "CRITICAL_RISK"
        elif jitter > 80 or rtt > 200:
            return "CONGESTED"
        elif rssi < -74:
            return "ATTENUATED"
        else:
            return "OPTIMAL"

    clean_df["target_state"] = clean_df.apply(label_sample, axis=1)

    X = clean_df[features]
    y = clean_df["target_state"]

    clf = RandomForestClassifier(n_estimators=50, random_state=42)
    clf.fit(X, y)
    
    clean_df["predicted_state"] = clf.predict(X)
    probabilities = clf.predict_proba(X)
    classes = list(clf.classes_)

    return clf, clean_df, classes


def generate_cc_dispatch_ticket(df, physical_summary):
    """
    Synthesizes physical telemetry into an official Computer & Communication Centre
    infrastructure remediation ticket.
    """
    active_bssid = df["bssid"].dropna().iloc[-1] if not df["bssid"].dropna().empty else "Unknown"
    active_ssid = df["ssid"].dropna().iloc[-1] if not df["ssid"].dropna().empty else "Unknown"
    active_band = df["band_ghz"].dropna().iloc[-1] if not df["band_ghz"].dropna().empty else 2.4
    active_ch = df["channel"].dropna().iloc[-1] if not df["channel"].dropna().empty else 1
    mean_rssi = df["rssi_dbm"].mean()
    mean_jitter = df["ping_jitter_ms"].mean()
    mean_loss = df["packet_loss_pct"].mean()

    # Determine primary root cause
    max_physical_delta = 0.0
    for loc, data in physical_summary.items():
        if data["physical_delta_dbm"] is not None and data["physical_delta_dbm"] > max_physical_delta:
            max_physical_delta = data["physical_delta_dbm"]

    remediation_actions = []

    if max_physical_delta >= 6.0:
        remediation_actions.append(
            f"[!] Physical Barrier Attenuation: Closed door induces {max_physical_delta} dBm path-loss. "
            f"Recommend: Increase AP Tx power by +3 dBm or deploy corridor AP bracket 1.5m closer to room cluster."
        )

    if active_band == 5.0 and mean_rssi < -75:
        remediation_actions.append(
            f"[!] Severe 5 GHz Penetration Loss ({mean_rssi:.1f} dBm). "
            f"Recommend: Lower 802.11k/v Roaming / Band-Steering RSSI threshold from -70 dBm to -78 dBm to allow graceful 2.4 GHz fallback."
        )
    elif active_band == 2.4 and mean_jitter > 70:
        remediation_actions.append(
            f"[!] 2.4 GHz Channel {active_ch} Co-Channel Contention (Mean Jitter: {mean_jitter:.1f} ms). "
            f"Recommend: Reassign AP BSSID {active_bssid} to non-overlapping Channel 1, 6, or 11."
        )
    else:
        remediation_actions.append(
            f"[i] Link parameters stable under normal conditions. Monitor for peak-hour spectral contention."
        )

    ticket_text = f"""
[bold cyan]Campus IT / Computer & Communication Centre (CC) Network Dispatch Ticket[/bold cyan]
--------------------------------------------------------------------------------
- Target AP (BSSID): [yellow]{active_bssid}[/yellow] (SSID: {active_ssid})
- Active Frequency:  [yellow]{active_band} GHz (Channel {active_ch})[/yellow]
- Telemetry Window:  [dim]{df['timestamp'].min()} to {df['timestamp'].max()}[/dim]
- Sample Count:      {len(df)} observations ({len(df[df['is_synthetic']==False])} real physical, {len(df[df['is_synthetic']==True])} synthetic)
- Observed RSSI:     Mean {mean_rssi:.1f} dBm (Min: {df['rssi_dbm'].min()} dBm, Max: {df['rssi_dbm'].max()} dBm)
- Latency & Jitter:  Mean RTT {df['ping_rtt_avg_ms'].mean():.1f} ms | Mean Jitter {mean_jitter:.1f} ms | Loss {mean_loss:.1f}%

[bold green]Physical Decomposition:[/bold green]
- Door Attenuation:  +{max_physical_delta} dBm drop when door is closed.

[bold magenta]Actionable Remediation Strategy for CC Network Ops:[/bold magenta]
"""
    for idx, action in enumerate(remediation_actions, 1):
        ticket_text += f"{idx}. {action}\n"

    return ticket_text


def main():
    parser = argparse.ArgumentParser(description="RF-Pulse AI Diagnostic Engine")
    parser.add_argument("--data", type=str, default="data/rf_pulse_dataset.parquet", help="Path to Parquet dataset")
    args = parser.parse_args()

    console.print(f"\n[bold green][*] Loading Telemetry from [cyan]{args.data}[/cyan]...[/bold green]")
    df = load_telemetry(args.data)
    console.print(f"[dim]Loaded {len(df)} telemetry records.[/dim]\n")

    # 1. Physical Attenuation Analysis
    physical_summary = compute_physical_attenuation(df)
    
    table = Table(title="Physical Barrier Decomposition (Door Attenuation)")
    table.add_column("Location Tag", style="cyan")
    table.add_column("Open RSSI", justify="right")
    table.add_column("Closed RSSI", justify="right")
    table.add_column("Delta (Loss)", justify="right", style="bold red")
    table.add_column("Tx Drop %", justify="right")
    table.add_column("Sample Count", justify="center")

    for loc, data in physical_summary.items():
        open_str = f"{data['avg_open_rssi']:.1f} dBm" if data['avg_open_rssi'] is not None else "N/A"
        closed_str = f"{data['avg_closed_rssi']:.1f} dBm" if data['avg_closed_rssi'] is not None else "N/A"
        delta_str = f"+{data['physical_delta_dbm']} dBm" if data['physical_delta_dbm'] is not None else "N/A"
        tx_str = f"{data['tx_drop_pct']}%" if data['tx_drop_pct'] is not None else "N/A"
        
        table.add_row(loc, open_str, closed_str, delta_str, tx_str, str(data['sample_count']))
    
    console.print(table)

    # 2. Train Link Health Model
    clf, analyzed_df, classes = train_link_health_classifier(df)
    state_counts = analyzed_df["predicted_state"].value_counts().to_dict()
    
    console.print("\n[bold green][*] AI Link Health Classification Distribution:[/bold green]")
    for state, count in state_counts.items():
        pct = (count / len(analyzed_df)) * 100
        console.print(f"  - [yellow]{state}[/yellow]: {count} samples ({pct:.1f}%)")

    # 3. Generate Official CC Dispatch Ticket
    ticket = generate_cc_dispatch_ticket(analyzed_df, physical_summary)
    console.print(Panel(ticket, title="Automated CC Engineering Ticket", border_style="cyan"))


if __name__ == "__main__":
    main()
