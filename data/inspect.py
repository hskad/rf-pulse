"""
RF-Pulse: Terminal Dataset Inspector (TUI)
Inspects parquet telemetry collected across campus environments.
Allows judges and engineers to verify physical data lineage,
measurements, and barrier attenuation without a browser.
"""

import argparse
import os
import pandas as pd
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

PARQUET_PATH = "data/rf_pulse_dataset.parquet"


def load_dataset():
    if not os.path.exists(PARQUET_PATH):
        console.print(f"[bold red]Error:[/bold red] Telemetry file not found at '{PARQUET_PATH}'.")
        console.print("Run data collector first: [cyan]python -m collector.scanner[/cyan]")
        raise SystemExit(1)
    return pd.read_parquet(PARQUET_PATH)


def display_metadata(df):
    file_size_kb = os.path.getsize(PARQUET_PATH) / 1024
    real_count = int((df["is_synthetic"] == False).sum())
    synth_count = int((df["is_synthetic"] == True).sum())
    total_count = len(df)
    unique_locs = df["location_tag"].nunique()

    meta_table = Table(box=None, padding=(0, 2), show_header=False)
    meta_table.add_column("Key", style="dim")
    meta_table.add_column("Value", style="bold white")
    meta_table.add_column("Key2", style="dim")
    meta_table.add_column("Value2", style="bold white")

    meta_table.add_row("Dataset File:", PARQUET_PATH, "File Size:", f"{file_size_kb:.1f} KB (Apache Parquet)")
    meta_table.add_row("Total Records:", f"{total_count} rows", "Schema:", f"{len(df.columns)} columns")
    meta_table.add_row(
        "Real Physical Obs:", f"[bold green]{real_count}[/bold green] (on-site scans)",
        "Synthetic Extension:", f"[dim]{synth_count}[/dim] (ITU-R calibrated)"
    )
    meta_table.add_row(
        "Unique Locations:", f"{unique_locs} test points",
        "Target SSID:", "R04-5B4A (2.4 GHz)"
    )

    console.print(
        Panel(
            meta_table,
            title="[bold yellow]RF-PULSE - CAMPUS TELEMETRY LAKE[/bold yellow]",
            subtitle="[dim]Physical AI Sensor Lineage | Apache Parquet[/dim]",
            border_style="cyan",
            expand=False,
            box=box.ROUNDED,
        )
    )


def display_physical_barrier_loss(df):
    room_df = df[df["location_tag"] == "Hostel_Room"]
    if room_df.empty:
        return

    open_df = room_df[room_df["door_state"] == "Open"]
    closed_df = room_df[room_df["door_state"] == "Closed"]

    if open_df.empty or closed_df.empty:
        return

    open_rssi = open_df["rssi_dbm"].mean()
    closed_rssi = closed_df["rssi_dbm"].mean()
    delta_rssi = open_rssi - closed_rssi

    open_tx = open_df["tx_rate_mbps"].mean()
    closed_tx = closed_df["tx_rate_mbps"].mean()
    tx_drop_pct = ((open_tx - closed_tx) / open_tx) * 100 if open_tx > 0 else 0

    loss_table = Table(box=None, show_header=False, padding=(0, 2))
    loss_table.add_column("Metric", style="dim")
    loss_table.add_column("Open State", style="white")
    loss_table.add_column("Closed State", style="white")
    loss_table.add_column("Delta (Barrier Loss)", style="bold yellow")

    loss_table.add_row(
        "Signal Strength (RSSI):",
        f"{open_rssi:.1f} dBm",
        f"{closed_rssi:.1f} dBm",
        f"+{delta_rssi:.1f} dBm drop ({2.0**(delta_rssi/3):.1f}x RF energy cut)"
    )
    loss_table.add_row(
        "Physical Link Speed:",
        f"{open_tx:.0f} Mbps",
        f"{closed_tx:.0f} Mbps",
        f"-{tx_drop_pct:.1f}% throughput penalty"
    )

    console.print(
        Panel(
            loss_table,
            title="[bold yellow]PHYSICAL BARRIER ISOLATION (Hostel Wooden Door)[/bold yellow]",
            subtitle="[dim]Controlled Variable Test - Room 5B4A[/dim]",
            border_style="yellow",
            expand=False,
            box=box.ROUNDED,
        )
    )


def display_location_summary(df, real_only=False):
    target_df = df[df["is_synthetic"] == False] if real_only else df
    title_suffix = " (Real Physical Measurements Only)" if real_only else " (All Observations)"

    table = Table(
        title=f"\n[bold]Location Physical Benchmarks{title_suffix}[/bold]",
        show_lines=True,
        header_style="bold cyan",
        box=box.ROUNDED,
    )

    table.add_column("Location Tag", style="white", min_width=20)
    table.add_column("Barrier", justify="center", style="dim")
    table.add_column("Type", justify="center")
    table.add_column("Count", justify="right")
    table.add_column("RSSI (dBm)", justify="right")
    table.add_column("Link (Mbps)", justify="right")
    table.add_column("RTT (ms)", justify="right")
    table.add_column("Link Status", justify="center")

    grouped = target_df.groupby(["location_tag", "door_state", "is_synthetic"]).agg({
        "rssi_dbm": "mean",
        "tx_rate_mbps": "mean",
        "ping_rtt_avg_ms": "mean",
        "timestamp": "count"
    }).reset_index()

    grouped = grouped.sort_values(by="rssi_dbm", ascending=False)

    for _, row in grouped.iterrows():
        rssi = row["rssi_dbm"]
        tx = row["tx_rate_mbps"]
        rtt = row["ping_rtt_avg_ms"]
        count = int(row["timestamp"])
        is_synth = row["is_synthetic"]

        if rssi >= -65 and tx >= 50:
            status = "[bold green]OPTIMAL[/bold green]"
            rssi_style = "bold green"
        elif rssi >= -80 and tx >= 20:
            status = "[bold yellow]ATTENUATED[/bold yellow]"
            rssi_style = "bold yellow"
        else:
            status = "[bold red]DEADZONE[/bold red]"
            rssi_style = "bold red"

        type_badge = "[dim]SYNTH[/dim]" if is_synth else "[bold green]REAL[/bold green]"

        table.add_row(
            str(row["location_tag"]),
            str(row["door_state"]),
            type_badge,
            str(count),
            f"[{rssi_style}]{rssi:.1f}[/{rssi_style}]",
            f"{tx:.0f}",
            f"{rtt:.0f}",
            status
        )

    console.print(table)


def display_telemetry_rows(df, real_only=False, limit=15):
    target_df = df[df["is_synthetic"] == False] if real_only else df
    target_df = target_df.sample(frac=1.0, random_state=42).head(limit)

    title_suffix = f" (Sample {min(limit, len(target_df))} of {len(df)} records, {'Real Only' if real_only else 'Mixed'})"

    table = Table(
        title=f"\n[bold]Raw Telemetry Stream{title_suffix}[/bold]",
        show_lines=False,
        header_style="bold cyan",
        box=box.SIMPLE,
    )

    table.add_column("Time", style="dim", width=8)
    table.add_column("Location", style="white", min_width=16)
    table.add_column("Door", style="dim", justify="center", width=6)
    table.add_column("Type", justify="center", width=5)
    table.add_column("RSSI", justify="right", width=6)
    table.add_column("Rate", justify="right", width=6)
    table.add_column("RTT", justify="right", width=5)
    table.add_column("Loss", justify="right", width=5)

    for _, r in target_df.iterrows():
        t_str = str(r["timestamp"])[11:19]
        is_synth = r["is_synthetic"]
        type_badge = "[dim]SIM[/dim]" if is_synth else "[bold green]REAL[/bold green]"

        rssi = r["rssi_dbm"]
        rssi_style = "green" if rssi >= -65 else ("yellow" if rssi >= -80 else "red")

        table.add_row(
            t_str,
            str(r["location_tag"]),
            str(r["door_state"]),
            type_badge,
            f"[{rssi_style}]{rssi:.1f}[/{rssi_style}]",
            f"{r['tx_rate_mbps']:.0f}M",
            f"{r['ping_rtt_avg_ms']:.0f}ms",
            f"{r['packet_loss_pct']:.0f}%",
        )

    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="RF-Pulse: Terminal Dataset Inspector")
    parser.add_argument("--real", action="store_true", help="Display only real physical measurements (120 rows)")
    parser.add_argument("--summary", action="store_true", help="Show only the location summary benchmarks")
    parser.add_argument("--limit", type=int, default=15, help="Number of sample records to print (default: 15)")
    args = parser.parse_args()

    df = load_dataset()
    display_metadata(df)
    display_physical_barrier_loss(df)
    display_location_summary(df, real_only=args.real)

    if not args.summary:
        display_telemetry_rows(df, real_only=args.real, limit=args.limit)

    console.print(
        "\n[dim]Terminal commands:[/dim]"
    )
    console.print("  [cyan]python -m data.inspect --real[/cyan]            [dim]# Inspect only 120 physical measurements[/dim]")
    console.print("  [cyan]python -m data.inspect --summary[/cyan]         [dim]# High-level location RF benchmarks[/dim]")
    console.print("  [cyan]python -m data.inspect --real --limit 120[/cyan] [dim]# Dump full real physical dataset[/dim]")
    console.print("  [cyan]http://localhost:8080[/cyan]                     [dim]# View web dashboard with filters[/dim]\n")


if __name__ == "__main__":
    main()
