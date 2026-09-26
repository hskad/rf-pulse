/**
 * RF-Pulse Frontend Application Controller
 * Handles real-time telemetry polling, on-demand probing, table filtering,
 * and AI diagnostics rendering.
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
  document.getElementById('btn-collect-open').addEventListener('click', () => triggerProbe('Desk', 'Open'));
  document.getElementById('btn-collect-closed').addEventListener('click', () => triggerProbe('Desk', 'Closed'));
  document.getElementById('btn-refresh').addEventListener('click', () => {
    fetchDiagnostics();
    fetchTelemetry();
  });

  document.getElementById('btn-copy-ticket').addEventListener('click', copyTicketToClipboard);

  // Filter button listeners
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      e.target.classList.add('active');
      currentFilter = e.target.getAttribute('data-filter');
      renderTelemetryTable();
    });
  });

  // Auto-refresh telemetry every 10 seconds
  setInterval(fetchDiagnostics, 10000);
}

async function fetchDiagnostics() {
  try {
    const res = await fetch('/api/diagnostics');
    if (!res.ok) return;
    const data = await res.json();
    renderLiveMetrics(data.latest_metrics);
    renderPhysicalDecomposition(data.physical_decomposition);
    renderHealthDistribution(data.health_distribution);
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

    document.getElementById('stat-total').innerText = data.total_rows || 0;
    document.getElementById('stat-real').innerText = `${data.real_count || 0} Real`;
    document.getElementById('stat-synth').innerText = `${data.synthetic_count || 0} Synthetic`;

    renderTelemetryTable();
  } catch (err) {
    console.error('Failed to fetch telemetry records:', err);
  }
}

function renderLiveMetrics(m) {
  if (!m) return;

  // Header chips
  document.getElementById('chip-ssid').innerText = m.ssid || 'Connected';
  document.getElementById('chip-band').innerText = `${m.band_ghz || 2.4} GHz`;
  document.getElementById('chip-channel').innerText = m.channel || '-';

  // Metrics
  const rssiEl = document.getElementById('val-rssi');
  rssiEl.innerText = m.rssi_dbm ? m.rssi_dbm.toFixed(1) : '--';
  const rssiPct = Math.min(Math.max((m.rssi_dbm + 100) * 2, 0), 100);
  const barRssi = document.getElementById('bar-rssi');
  barRssi.style.width = `${rssiPct}%`;

  if (m.rssi_dbm > -65) {
    barRssi.style.background = 'var(--accent-emerald)';
    document.getElementById('footer-rssi').innerText = 'Signal Quality: Excellent (Line-of-Sight)';
  } else if (m.rssi_dbm > -78) {
    barRssi.style.background = 'var(--accent-amber)';
    document.getElementById('footer-rssi').innerText = 'Signal Quality: Moderate (Barrier Attenuation)';
  } else {
    barRssi.style.background = 'var(--accent-rose)';
    document.getElementById('footer-rssi').innerText = 'Signal Quality: Poor (Severe Deadzone)';
  }

  document.getElementById('val-tx').innerText = m.tx_rate_mbps ? m.tx_rate_mbps.toFixed(1) : '--';
  document.getElementById('val-rtt').innerText = m.ping_rtt_avg_ms ? m.ping_rtt_avg_ms.toFixed(0) : '--';
  document.getElementById('footer-rtt').innerText = `Jitter: ${m.ping_jitter_ms || 0} ms · Loss: ${m.packet_loss_pct || 0}%`;

  document.getElementById('val-bssid').innerText = m.bssid || '--:--:--:--';
  document.getElementById('val-ssid').innerText = m.ssid || '--';
}

function renderPhysicalDecomposition(decomp) {
  if (!decomp) return;
  const tbody = document.getElementById('tbody-attenuation');
  tbody.innerHTML = '';

  let maxDrop = 0;
  for (const [loc, d] of Object.entries(decomp)) {
    const tr = document.createElement('tr');
    const openRssi = d.avg_open_rssi ? `${d.avg_open_rssi.toFixed(1)} dBm` : '<span style="color:var(--text-dim)">N/A</span>';
    const closedRssi = d.avg_closed_rssi ? `${d.avg_closed_rssi.toFixed(1)} dBm` : '<span style="color:var(--text-dim)">N/A</span>';
    const drop = d.physical_delta_dbm !== null ? `+${d.physical_delta_dbm} dBm` : '<span style="color:var(--text-dim)">--</span>';
    const txDrop = d.tx_drop_pct !== null ? `${d.tx_drop_pct}%` : '<span style="color:var(--text-dim)">--</span>';

    if (d.physical_delta_dbm && d.physical_delta_dbm > maxDrop) {
      maxDrop = d.physical_delta_dbm;
    }

    tr.innerHTML = `
      <td><strong>${loc}</strong></td>
      <td>${openRssi}</td>
      <td>${closedRssi}</td>
      <td style="color:var(--accent-rose); font-weight:600">${drop}</td>
      <td>${txDrop}</td>
      <td>${d.sample_count}</td>
    `;
    tbody.appendChild(tr);
  }

  const doorDeltaEl = document.getElementById('val-door-delta');
  if (maxDrop > 0) {
    doorDeltaEl.innerText = `+${maxDrop.toFixed(1)} dBm`;
    doorDeltaEl.style.color = 'var(--accent-rose)';
    document.getElementById('desc-door-delta').innerText =
      `Physical barrier absorption detected. Closed door accounts for a ${maxDrop.toFixed(1)} dBm RSSI degradation.`;
  } else {
    doorDeltaEl.innerText = 'Calculating...';
    document.getElementById('desc-door-delta').innerText =
      'Collect samples with door Open and Closed to calculate physical barrier delta.';
  }
}

function renderHealthDistribution(dist) {
  if (!dist) return;
  const container = document.getElementById('health-distribution-bars');
  container.innerHTML = '';

  const total = Object.values(dist).reduce((a, b) => a + b, 0) || 1;
  const colorMap = {
    'OPTIMAL': 'state-green',
    'ATTENUATED': 'state-amber',
    'CONGESTED': 'state-blue',
    'CRITICAL_RISK': 'state-red'
  };

  for (const [state, count] of Object.entries(dist)) {
    const pct = ((count / total) * 100).toFixed(1);
    const colorClass = colorMap[state] || 'state-blue';

    const row = document.createElement('div');
    row.className = 'health-state-row';
    row.innerHTML = `
      <span class="state-name">${state}</span>
      <div class="state-bar-bg">
        <div class="state-bar-fill ${colorClass}" style="width: ${pct}%;"></div>
      </div>
      <span class="state-val">${pct}%</span>
    `;
    container.appendChild(row);
  }

  // Set AI Verdict
  const verdictEl = document.getElementById('ai-verdict');
  if (dist['CRITICAL_RISK'] && dist['CRITICAL_RISK'] > total * 0.4) {
    verdictEl.innerHTML = `⚠️ <strong>High Drop Risk:</strong> Over 40% of observations exhibit critical RSSI / packet drops. Physical AP repositioning or 5 GHz band fallback advised.`;
    verdictEl.style.borderColor = 'rgba(244, 63, 94, 0.4)';
    verdictEl.style.background = 'rgba(244, 63, 94, 0.1)';
  } else if (dist['CONGESTED'] && dist['CONGESTED'] > total * 0.3) {
    verdictEl.innerHTML = `📶 <strong>Spectral Contention:</strong> Significant jitter detected despite acceptable RSSI. Co-channel interference on 2.4 GHz active.`;
    verdictEl.style.borderColor = 'rgba(245, 158, 11, 0.4)';
    verdictEl.style.background = 'rgba(245, 158, 11, 0.1)';
  } else {
    verdictEl.innerHTML = `✅ <strong>Operational Link:</strong> Physical RSSI and latency within acceptable operational margins for remote learning/streaming.`;
    verdictEl.style.borderColor = 'rgba(16, 185, 129, 0.4)';
    verdictEl.style.background = 'rgba(16, 185, 129, 0.1)';
  }
}

function renderTicket(ticketText) {
  if (!ticketText) return;
  document.getElementById('ticket-content').innerText = ticketText;
}

function renderTelemetryTable() {
  const tbody = document.getElementById('tbody-telemetry');
  tbody.innerHTML = '';

  let filtered = currentTelemetry;
  if (currentFilter === 'real') {
    filtered = currentTelemetry.filter(r => r.is_synthetic === false);
  } else if (currentFilter === 'synthetic') {
    filtered = currentTelemetry.filter(r => r.is_synthetic === true);
  }

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" class="text-center">No telemetry records match filter "${currentFilter}".</td></tr>`;
    return;
  }

  // Show newest first
  const displayRecords = [...filtered].reverse().slice(0, 50);

  displayRecords.forEach(r => {
    const tr = document.createElement('tr');
    const timeStr = r.timestamp ? r.timestamp.substring(11, 19) : '--';
    const typeBadge = r.is_synthetic
      ? `<span class="badge" style="color:var(--accent-purple); border-color:var(--accent-purple)">Synthetic</span>`
      : `<span class="badge" style="color:var(--accent-emerald); border-color:var(--accent-emerald)">Real Edge</span>`;

    tr.innerHTML = `
      <td style="font-family:var(--font-mono); font-size:0.78rem">${timeStr}</td>
      <td>${typeBadge}</td>
      <td><strong>${r.location_tag || 'Desk'}</strong></td>
      <td>${r.door_state || 'Open'}</td>
      <td style="font-family:var(--font-mono); font-weight:600">${r.rssi_dbm ? r.rssi_dbm.toFixed(1) + ' dBm' : '--'}</td>
      <td>${r.tx_rate_mbps ? r.tx_rate_mbps.toFixed(0) + ' Mbps' : '--'}</td>
      <td>${r.ping_rtt_avg_ms ? r.ping_rtt_avg_ms.toFixed(0) + ' ms' : '--'}</td>
      <td>${r.ping_jitter_ms ? r.ping_jitter_ms.toFixed(0) + ' ms' : '--'}</td>
      <td>${r.packet_loss_pct || 0}%</td>
    `;
    tbody.appendChild(tr);
  });
}

async function triggerProbe(location, door) {
  const btn = door === 'Open' ? document.getElementById('btn-collect-open') : document.getElementById('btn-collect-closed');
  const originalHtml = btn.innerHTML;
  btn.innerHTML = `<span class="btn-icon">⏳</span> Probing RF...`;
  btn.disabled = true;

  try {
    const res = await fetch('/api/collect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ location: location, door: door, samples: 3 })
    });
    const result = await res.json();
    if (result.status === 'success') {
      await fetchDiagnostics();
      await fetchTelemetry();
    } else {
      alert(`Error collecting sample: ${result.error}`);
    }
  } catch (err) {
    alert(`Failed to trigger probe: ${err.message}`);
  } finally {
    btn.innerHTML = originalHtml;
    btn.disabled = false;
  }
}

function copyTicketToClipboard() {
  const text = document.getElementById('ticket-content').innerText;
  navigator.clipboard.writeText(text).then(() => {
    const btn = document.getElementById('btn-copy-ticket');
    btn.innerText = '✓ Copied!';
    setTimeout(() => {
      btn.innerText = '📋 Copy Ticket to Clipboard';
    }, 2000);
  });
}
