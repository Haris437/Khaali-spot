// ── Section Navigation ────────────────────────────────────────────────────────
function showSection(name) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  document.getElementById('section-' + name).classList.add('active');
  document.getElementById('section-title').textContent =
    name.charAt(0).toUpperCase() + name.slice(1);

  event.currentTarget.classList.add('active');
}

// ── Clock ─────────────────────────────────────────────────────────────────────
function updateClock() {
  const now = new Date();
  document.getElementById('headerTime').textContent =
    now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}
setInterval(updateClock, 1000);
updateClock();

// ── Update stat cards with real data ─────────────────────────────────────────
function updateStats(data) {
  document.getElementById('total').textContent    = data.total_chairs;
  document.getElementById('free').textContent     = data.free;
  document.getElementById('occupied').textContent = data.occupied;
  document.getElementById('percent').textContent  = data.occupancy_percent + '%';
  document.getElementById('progressBar').style.width = data.occupancy_percent + '%';
  document.getElementById('progressLabel').textContent = data.occupancy_percent + '%';
}

// ── Fetch live stats every 3 seconds ─────────────────────────────────────────
function fetchStats() {
  fetch('/status')
    .then(r => r.json())
    .then(data => updateStats(data))
    .catch(err => console.error('Stats error:', err));
}
setInterval(fetchStats, 3000);
fetchStats();

// ── Refresh snapshot image ────────────────────────────────────────────────────
function refreshSnapshot() {
  fetch('/snapshot?t=' + Date.now())
    .then(res => {
      if (res.status === 204) return;
      if (res.ok) {
        const img = document.getElementById('liveFeed');
        const placeholder = document.getElementById('feedPlaceholder');
        img.src = '/snapshot?t=' + Date.now();
        img.style.display = 'block';
        if (placeholder) placeholder.style.display = 'none';
        document.getElementById('lastUpdated').textContent =
          'Updated at ' + new Date().toLocaleTimeString();
      }
    });
}
setInterval(refreshSnapshot, 3000);

// ── Add row to history table ──────────────────────────────────────────────────
function addHistoryRow(data) {
  const tbody = document.getElementById('historyBody');
  const time  = new Date().toLocaleTimeString();

  // Remove "no history" placeholder if present
  if (tbody.rows[0] && tbody.rows[0].cells[0].colSpan === 5) {
    tbody.innerHTML = '';
  }

  const row = `<tr>
    <td>${time}</td>
    <td>${data.total_chairs}</td>
    <td style="color:#00e676">${data.free}</td>
    <td style="color:#ff5252">${data.occupied}</td>
    <td>${data.occupancy_percent}%</td>
  </tr>`;

  tbody.insertAdjacentHTML('afterbegin', row);
}

// ── Quick Upload (Overview section) ──────────────────────────────────────────
function quickUploadImage() {
  const fileInput  = document.getElementById('quickUpload');
  const statusEl   = document.getElementById('uploadStatus');
  const nameEl     = document.getElementById('uploadFileName');

  if (!fileInput.files.length) {
    fileInput.click();
    return;
  }

  nameEl.textContent = fileInput.files[0].name;
  statusEl.textContent = '⏳ Analysing...';

  const formData = new FormData();
  formData.append('image', fileInput.files[0]);

  fetch('/upload', { method: 'POST', body: formData })
    .then(r => r.json())
    .then(data => {
      if (data.error) { statusEl.textContent = '❌ ' + data.error; return; }
      updateStats(data);
      refreshSnapshot();
      addHistoryRow(data);
      statusEl.textContent = `✅ Free: ${data.free} | Occupied: ${data.occupied} | Total: ${data.total_chairs}`;
    })
    .catch(() => { statusEl.textContent = '❌ Upload failed. Try again.'; });
}

// ── Full Upload (Upload section) ──────────────────────────────────────────────
function updateFileName() {
  const f = document.getElementById('fullUpload').files[0];
  if (f) document.getElementById('fullUploadFileName').textContent = f.name;
}

function fullUploadImage() {
  const fileInput = document.getElementById('fullUpload');
  const statusEl  = document.getElementById('fullUploadStatus');
  const resultImg = document.getElementById('fullUploadResult');

  if (!fileInput.files.length) { fileInput.click(); return; }

  statusEl.textContent = '⏳ Analysing image...';

  const formData = new FormData();
  formData.append('image', fileInput.files[0]);

  fetch('/upload', { method: 'POST', body: formData })
    .then(r => r.json())
    .then(data => {
      if (data.error) { statusEl.textContent = '❌ ' + data.error; return; }
      updateStats(data);
      addHistoryRow(data);
      statusEl.textContent = `✅ Free: ${data.free} | Occupied: ${data.occupied} | Total: ${data.total_chairs}`;
      resultImg.src = '/snapshot?t=' + Date.now();
      resultImg.style.display = 'block';

      const img = document.getElementById('liveFeed');
      const placeholder = document.getElementById('feedPlaceholder');
      img.src = '/snapshot?t=' + Date.now();
      img.style.display = 'block';
      if (placeholder) placeholder.style.display = 'none';
    })
    .catch(() => { statusEl.textContent = '❌ Upload failed.'; });
}
