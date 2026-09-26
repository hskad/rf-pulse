/**
 * RF-Pulse Frontend Application Controller (Granica Minimalist Edition)
 * Fetches Parquet telemetry, updates 3-column metric grid, and formats the CC ticket.
 */

let currentTelemetry = [];
let currentFilter = 'all';

document.addEventListener('DOMContentLoaded', () => {
  initApp();
});

function initApp() {
  fetchDiagnostics();
  fetchTelemetry();

  // Attach button listeners
  document.getElementById('btn-refresh').addEventListener('click', () => {
    fetchDiagnostics();
    fetchTelemetry();
  });

  document.getElementById('btn-copy-ticket').addEventListener('click', copyTicketToClipboard);

  // Polling every 12 seconds
  setInterval(fetchDiagnostics, 12000);
}

async function fetchDiagnostics() {
  try {
    const res = await fetch('/api/diagnostics');
    if (!res.ok) return;
    const data = await res.json();
    renderLiveMetrics(data.latest_metrics, data.physical_decomposition);
    renderTicket(data.ticket);
  } catch (err) {
    console.error('Failed to fetch diagnostics:', err);
  }
}

async function fetchTelemetry() {
  try {
    const res = await fetch('/api/telemetry');
    if (!res.ok) return;
    const data = await res.json();
    currentTelemetry = data.records || [];

    const totalEl = document.getElementById('nav-total-count');
    if (totalEl) totalEl.innerText = data.total_rows || 0;
    const realEl = document.getElementById('nav-real-count');
    if (realEl) realEl.innerText = data.real_count || 0;

    renderTelemetryTable();
  } catch (err) {
    console.error('Failed to fetch telemetry records:', err);
  }
}

function renderLiveMetrics(m, decomp) {
  if (!m) return;

  // Header meta
  const ssidEl = document.getElementById('nav-ssid');
  if (ssidEl) ssidEl.innerText = m.ssid || 'Connected';
  const bandEl = document.getElementById('nav-band');
  if (bandEl) bandEl.innerText = `${m.band_ghz || 2.4} GHz Ch ${m.channel || '-'}`;

  // Metric 1: Observed RSSI
  const rssiEl = document.getElementById('val-rssi');
  rssiEl.innerHTML = `${m.rssi_dbm ? m.rssi_dbm.toFixed(1) : '--'} <span class="unit">dBm</span>`;
  document.getElementById('detail-rssi').innerText = 
    `BSSID: ${m.bssid || 'Unknown'} · Negotiated PHY: ${m.tx_rate_mbps ? m.tx_rate_mbps.toFixed(0) : '--'} Mbps`;

  // Metric 2: Physical Door Attenuation
  let maxDrop = null;
  if (decomp) {
    for (const [loc, d] of Object.entries(decomp)) {
      if (d.physical_delta_dbm !== null && (maxDrop === null || d.physical_delta_dbm > maxDrop)) {
        maxDrop = d.physical_delta_dbm;
      }
    }
  }

  const doorLossEl = document.getElementById('val-door-loss');
  if (maxDrop !== null && maxDrop > 0) {
    doorLossEl.innerHTML = `+${maxDrop.toFixed(1)} <span class="unit">dBm</span>`;
    document.getElementById('detail-door-loss').innerText = 
      `Empirical attenuation delta between line-of-sight and closed wooden barrier.`;
  } else {
    doorLossEl.innerHTML = `~5.5 <span class="unit">dBm</span>`;
    document.getElementById('detail-door-loss').innerText = 
      `Awaiting closed-door sample (or using empirical default).`;
  }

  // Metric 3: Latency & Jitter
  const rttEl = document.getElementById('val-rtt');
  rttEl.innerHTML = `${m.ping_rtt_avg_ms ? m.ping_rtt_avg_ms.toFixed(0) : '--'} <span class="unit">ms</span>`;
  document.getElementById('detail-rtt').innerText = 
    `Latency jitter: ${m.ping_jitter_ms ? m.ping_jitter_ms.toFixed(0) : '0'} ms · Packet drop: ${m.packet_loss_pct || 0}%`;
}

function renderTicket(ticketText) {
  if (!ticketText) return;
  document.getElementById('ticket-content').innerText = ticketText;
}

function renderTelemetryTable() {
  const tbody = document.getElementById('tbody-telemetry');
  tbody.innerHTML = '';

  if (!currentTelemetry || currentTelemetry.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 20px;">No telemetry records available.</td></tr>`;
    return;
  }

  // Show newest first (limit 50)
  const displayRecords = [...currentTelemetry].reverse().slice(0, 50);

  displayRecords.forEach(r => {
    const tr = document.createElement('tr');
    const timeStr = r.timestamp ? r.timestamp.substring(11, 19) : '--';

    tr.innerHTML = `
      <td style="font-family:var(--font-mono); font-size:11px;">${timeStr}</td>
      <td><strong>${r.location_tag || 'Desk'}</strong></td>
      <td>${r.door_state || 'Open'}</td>
      <td style="font-family:var(--font-mono); font-weight:600; color:var(--text-main);">${r.rssi_dbm ? r.rssi_dbm.toFixed(1) : '--'}</td>
      <td style="font-family:var(--font-mono);">${r.tx_rate_mbps ? r.tx_rate_mbps.toFixed(0) + ' Mbps' : '--'}</td>
      <td style="font-family:var(--font-mono);">${r.ping_rtt_avg_ms ? r.ping_rtt_avg_ms.toFixed(0) : '--'}</td>
      <td style="font-family:var(--font-mono);">${r.ping_jitter_ms ? r.ping_jitter_ms.toFixed(0) : '0'}</td>
      <td style="font-family:var(--font-mono);">${r.packet_loss_pct || 0}%</td>
    `;
    tbody.appendChild(tr);
  });
}

function copyTicketToClipboard() {
  const text = document.getElementById('ticket-content').innerText;
  navigator.clipboard.writeText(text).then(() => {
    const btn = document.getElementById('btn-copy-ticket');
    btn.innerText = 'COPIED TO CLIPBOARD';
    setTimeout(() => {
      btn.innerText = 'COPY DIRECTIVE';
    }, 2000);
  });
}
