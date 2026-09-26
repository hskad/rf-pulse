"""
RF-Pulse: Automated Edge Wi-Fi Physical Probe
Queries native Windows networking interfaces and ICMP diagnostics,
formatting raw physical RF observations into structured Parquet records.
"""

import argparse
import datetime
import os
import re
import subprocess
import time
import uuid
import pandas as pd
from rich.console import Console
from rich.table import Table

console = Console()


def get_wlan_interfaces():
    """Runs `netsh wlan show interfaces` and extracts physical RF metrics."""
    try:
        cmd = ["netsh", "wlan", "show", "interfaces"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout

        data = {
            "ssid": None,
            "bssid": None,
            "band_ghz": None,
            "channel": None,
            "radio_type": None,
            "rx_rate_mbps": None,
            "tx_rate_mbps": None,
            "signal_pct": None,
            "rssi_dbm": None,
            "status": "disconnected"
        }

        for line in output.splitlines():
            line = line.strip()
            if ":" not in line:
                continue
            key, val = [x.strip() for x in line.split(":", 1)]

            if key.lower() == "state" and "connected" in val.lower():
                data["status"] = "connected"
            elif key.lower() == "ssid":
                data["ssid"] = val
            elif "bssid" in key.lower():
                data["bssid"] = val
            elif key.lower() == "band":
                match = re.search(r"([0-9.]+)\s*ghz", val, re.IGNORECASE)
                if match:
                    data["band_ghz"] = float(match.group(1))
            elif key.lower() == "channel":
                match = re.search(r"\d+", val)
                if match:
                    data["channel"] = int(match.group(0))
            elif key.lower() == "radio type":
                data["radio_type"] = val
            elif "receive rate" in key.lower():
                match = re.search(r"([0-9.]+)", val)
                if match:
                    data["rx_rate_mbps"] = float(match.group(1))
            elif "transmit rate" in key.lower():
                match = re.search(r"([0-9.]+)", val)
                if match:
                    data["tx_rate_mbps"] = float(match.group(1))
            elif key.lower() == "signal":
                match = re.search(r"(\d+)%", val)
                if match:
                    data["signal_pct"] = int(match.group(1))
            elif key.lower() == "rssi":
                match = re.search(r"(-?\d+)", val)
                if match:
                    data["rssi_dbm"] = float(match.group(1))

        # Fallback for RSSI calculation if not directly exposed
        if data["rssi_dbm"] is None and data["signal_pct"] is not None:
            data["rssi_dbm"] = round((data["signal_pct"] / 2.0) - 100.0, 1)

        return data
    except Exception as e:
        console.print(f"[bold red]Error querying WLAN interfaces:[/bold red] {e}")
        return None


def get_ping_metrics(target="8.8.8.8", count=4):
    """Executes ICMP ping and computes average RTT, jitter, and packet loss."""
    try:
        cmd = ["ping", f"-n", str(count), target]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout

        metrics = {
            "ping_target": target,
            "ping_rtt_min_ms": None,
            "ping_rtt_max_ms": None,
            "ping_rtt_avg_ms": None,
            "ping_jitter_ms": None,
            "packet_loss_pct": 0.0
        }

        # Match Loss: Lost = 0 (0% loss)
        loss_match = re.search(r"\((\d+)%\s*loss\)", output, re.IGNORECASE)
        if loss_match:
            metrics["packet_loss_pct"] = float(loss_match.group(1))

        # Match RTT times: Minimum = 92ms, Maximum = 244ms, Average = 144ms
        rtt_match = re.search(
            r"Minimum\s*=\s*(\d+)ms,\s*Maximum\s*=\s*(\d+)ms,\s*Average\s*=\s*(\d+)ms",
            output,
            re.IGNORECASE
        )
        if rtt_match:
            min_rtt = float(rtt_match.group(1))
            max_rtt = float(rtt_match.group(2))
            avg_rtt = float(rtt_match.group(3))
            metrics["ping_rtt_min_ms"] = min_rtt
            metrics["ping_rtt_max_ms"] = max_rtt
            metrics["ping_rtt_avg_ms"] = avg_rtt
            metrics["ping_jitter_ms"] = round(max_rtt - min_rtt, 1)

        return metrics
    except Exception as e:
        return {
            "ping_target": target,
            "ping_rtt_min_ms": None,
            "ping_rtt_max_ms": None,
            "ping_rtt_avg_ms": None,
            "ping_jitter_ms": None,
            "packet_loss_pct": 100.0
        }


def collect_sample(location_tag, door_state, ping_target="8.8.8.8", session_id=None):
    """Collects a single observation combining WLAN physical properties and network health."""
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    wlan = get_wlan_interfaces()
    ping = get_ping_metrics(target=ping_target)

    record = {
        "timestamp": timestamp,
        "session_id": session_id or str(uuid.uuid4())[:8],
        "location_tag": location_tag,
        "door_state": door_state,
        "is_synthetic": False,
        "ssid": wlan.get("ssid") if wlan else None,
        "bssid": wlan.get("bssid") if wlan else None,
        "band_ghz": wlan.get("band_ghz") if wlan else None,
        "channel": wlan.get("channel") if wlan else None,
        "radio_type": wlan.get("radio_type") if wlan else None,
        "signal_pct": wlan.get("signal_pct") if wlan else None,
        "rssi_dbm": wlan.get("rssi_dbm") if wlan else None,
        "tx_rate_mbps": wlan.get("tx_rate_mbps") if wlan else None,
        "rx_rate_mbps": wlan.get("rx_rate_mbps") if wlan else None,
        "ping_rtt_avg_ms": ping.get("ping_rtt_avg_ms"),
        "ping_jitter_ms": ping.get("ping_jitter_ms"),
        "packet_loss_pct": ping.get("packet_loss_pct")
    }
    return record


def save_to_parquet(records, output_path="data/rf_pulse_dataset.parquet"):
    """Appends records to existing parquet dataset or creates a new one."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_new = pd.DataFrame(records)

    if os.path.exists(output_path):
        df_existing = pd.read_parquet(output_path)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_combined = df_new

    df_combined.to_parquet(output_path, engine="pyarrow", index=False)
    return len(df_combined)


def main():
    parser = argparse.ArgumentParser(description="RF-Pulse Edge Probe Collector")
    parser.add_argument("--location", type=str, default="Desk", help="Physical location in room (Desk, Bed, Doorway, Window)")
    parser.add_argument("--door", type=str, choices=["Open", "Closed"], default="Open", help="Physical state of room door")
    parser.add_argument("--samples", type=int, default=5, help="Number of samples to collect")
    parser.add_argument("--interval", type=int, default=2, help="Interval in seconds between samples")
    parser.add_argument("--output", type=str, default="data/rf_pulse_dataset.parquet", help="Path to output Parquet file")
    parser.add_argument("--target", type=str, default="8.8.8.8", help="Ping target (gateway/DNS)")
    args = parser.parse_args()

    session_id = f"{args.location.lower()}_{args.door.lower()}_{str(uuid.uuid4())[:6]}"

    console.print(f"\n[bold green][*] Starting RF-Pulse Physical Probe Session[/bold green]: [cyan]{session_id}[/cyan]")
    console.print(f"- Location: [yellow]{args.location}[/yellow] | Door: [yellow]{args.door}[/yellow]")
    console.print(f"- Samples: [yellow]{args.samples}[/yellow] | Interval: [yellow]{args.interval}s[/yellow]")
    console.print(f"- Target Output: [yellow]{args.output}[/yellow]\n")

    records = []
    table = Table(title="Live Edge Observations")
    table.add_column("Time (UTC)", style="dim")
    table.add_column("BSSID", style="cyan")
    table.add_column("Band", justify="center")
    table.add_column("Ch", justify="center")
    table.add_column("RSSI (dBm)", justify="right", style="bold")
    table.add_column("Tx (Mbps)", justify="right")
    table.add_column("RTT (ms)", justify="right")
    table.add_column("Jitter", justify="right")
    table.add_column("Loss %", justify="right")

    for i in range(args.samples):
        record = collect_sample(
            location_tag=args.location,
            door_state=args.door,
            ping_target=args.target,
            session_id=session_id
        )
        records.append(record)

        time_str = record["timestamp"].strftime("%H:%M:%S")
        rssi_str = f"{record['rssi_dbm']} dBm" if record['rssi_dbm'] is not None else "N/A"
        tx_str = f"{record['tx_rate_mbps']}" if record['tx_rate_mbps'] is not None else "N/A"
        rtt_str = f"{record['ping_rtt_avg_ms']}ms" if record['ping_rtt_avg_ms'] is not None else "Timeout"
        jitter_str = f"{record['ping_jitter_ms']}ms" if record['ping_jitter_ms'] is not None else "N/A"
        loss_str = f"{record['packet_loss_pct']}%"

        table.add_row(
            time_str,
            str(record["bssid"]),
            f"{record['band_ghz']} GHz",
            str(record["channel"]),
            rssi_str,
            tx_str,
            rtt_str,
            jitter_str,
            loss_str
        )

        if i < args.samples - 1:
            time.sleep(args.interval)

    console.print(table)
    total_rows = save_to_parquet(records, args.output)
    console.print(f"\n[bold green][OK] Successfully persisted {len(records)} observations to Parquet.[/bold green]")
    console.print(f"[bold cyan]Total dataset size: {total_rows} rows in {args.output}[/bold cyan]\n")


if __name__ == "__main__":
    main()
