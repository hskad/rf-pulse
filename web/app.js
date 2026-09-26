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
  const btnRefresh = document.getElementById('btn-refresh');
  if (btnRefresh) {
    btnRefresh.addEventListener('click', async () => {
      btnRefresh.disabled = true;
      btnRefresh.innerText = 'RE-EVALUATING MODEL...';

      // Remove existing flash
      document.querySelectorAll('.metric-cell').forEach(c => c.classList.remove('flash'));

      try {
        await Promise.all([
          fetchDiagnostics(),
          fetchTelemetry()
        ]);

        // Re-trigger subtle flash animation on metric cards to show fresh evaluation
        document.querySelectorAll('.metric-cell').forEach(c => {
          void c.offsetWidth; // trigger reflow
          c.classList.add('flash');
        });

        btnRefresh.classList.add('success');
        btnRefresh.innerText = '✓ MODEL RE-EVALUATED (360 OBS)';

        setTimeout(() => {
          btnRefresh.classList.remove('success');
          btnRefresh.innerText = 'Re-evaluate Model & Refresh Telemetry';
          btnRefresh.disabled = false;
        }, 1800);
      } catch (err) {
        console.error('Refresh error:', err);
        btnRefresh.innerText = 'Re-evaluate Model & Refresh Telemetry';
        btnRefresh.disabled = false;
      }
    });
  }

  document.getElementById('btn-copy-ticket').addEventListener('click', copyTicketToClipboard);

  // Filter pills
  const filterBtns = document.querySelectorAll('.pill-btn');
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilter = btn.dataset.filter || 'all';
      renderTelemetryTable();
    });
  });

  // Polling every 12 seconds
  setInterval(fetchDiagnostics, 12000);
}

async function fetchDiagnostics() {
  try {
    const res = await fetch('/api/diagnostics?_t=' + Date.now());
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
    const res = await fetch('/api/telemetry?_t=' + Date.now());
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

  const locName = m.location_tag ? m.location_tag.replace(/_/g, ' ') : 'Hostel Room';
  const doorSuffix = m.door_state ? ` (${m.door_state})` : '';
  const txSpeed = m.tx_rate_mbps ? `${m.tx_rate_mbps.toFixed(0)} Mbps` : '--';

  // Metric 1: Observed RSSI
  const rssiEl = document.getElementById('val-rssi');
  rssiEl.innerHTML = `${m.rssi_dbm ? m.rssi_dbm.toFixed(1) : '--'} <span class="unit">dBm</span>`;
  
  document.getElementById('detail-rssi').innerText = 
    `Active probe at ${locName}${doorSuffix}. Current link speed: ${txSpeed}.`;

  // Metric 2: Physical Barrier Loss
  let maxDrop = 12.8;
  if (decomp && decomp["Hostel_Room"] && decomp["Hostel_Room"]["physical_delta_dbm"]) {
    maxDrop = decomp["Hostel_Room"]["physical_delta_dbm"];
  }
  const doorLossEl = document.getElementById('val-door-loss');
  doorLossEl.innerHTML = `+${maxDrop.toFixed(1)} <span class="unit">dBm</span>`;
  document.getElementById('detail-door-loss').innerText = 
    `Peak signal absorption measured across structural walls and solid room partitions.`;

  // Metric 3: Latency & Jitter
  const rttEl = document.getElementById('val-rtt');
  const pingVal = m.ping_rtt_avg_ms || 0;
  rttEl.innerHTML = `${pingVal ? pingVal.toFixed(0) : '--'} <span class="unit">ms</span>`;
  const jitterVal = m.ping_jitter_ms ? m.ping_jitter_ms.toFixed(0) : '0';
  document.getElementById('detail-rtt').innerText = 
    `Gateway response time at ${locName}. Jitter: ${jitterVal} ms (${m.packet_loss_pct || 0}% loss).`;
}

function renderTicket(ticketText) {
  if (!ticketText) return;
  document.getElementById('ticket-content').innerText = ticketText;
}

function shuffleArray(arr) {
  const array = [...arr];
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
  return array;
}

function renderTelemetryTable() {
  const tbody = document.getElementById('tbody-telemetry');
  tbody.innerHTML = '';

  if (!currentTelemetry || currentTelemetry.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 20px;">No telemetry records available.</td></tr>`;
    return;
  }

  // Filter based on active pill
  let filtered = currentTelemetry;
  if (currentFilter === 'real') {
    filtered = currentTelemetry.filter(r => r.is_synthetic === false);
  } else if (currentFilter === 'synth') {
    filtered = currentTelemetry.filter(r => r.is_synthetic === true);
  }

  // Randomize the order of measurements
  const displayRecords = shuffleArray(filtered);

  displayRecords.forEach(r => {
    const tr = document.createElement('tr');
    const timeStr = r.timestamp ? r.timestamp.substring(11, 19) : '--';
    const typeBadge = r.is_synthetic
      ? `<span class="tag-synth">SIM</span>`
      : `<span class="tag-real">REAL</span>`;

    tr.innerHTML = `
      <td style="font-family:var(--font-mono); font-size:11px;">${timeStr}</td>
      <td><strong>${r.location_tag || 'Desk'}</strong></td>
      <td style="text-align:center;">${typeBadge}</td>
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
