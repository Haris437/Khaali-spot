// ── Auto-refresh stats every 3 seconds ──────────────────────────────────────
function fetchStats() {
  fetch("/status")
    .then(res => res.json())
    .then(data => {
      document.getElementById("total").textContent    = data.total_chairs;
      document.getElementById("free").textContent     = data.free;
      document.getElementById("occupied").textContent = data.occupied;
      document.getElementById("percent").textContent  = data.occupancy_percent + "%";

      // Update progress bar width
      document.getElementById("progressBar").style.width = data.occupancy_percent + "%";
    })
    .catch(err => console.error("Stats fetch error:", err));
}

// ── Refresh live camera snapshot every 3 seconds ─────────────────────────────
function refreshSnapshot() {
  const img = document.getElementById("liveFeed");
  // Append timestamp to prevent browser caching the old image
  img.src = "/snapshot?t=" + new Date().getTime();
}

// Start polling
setInterval(fetchStats,      3000);
setInterval(refreshSnapshot, 3000);

// Run once immediately on page load
fetchStats();
refreshSnapshot();


// ── Demo Mode: Upload Image ───────────────────────────────────────────────────
function uploadImage() {
  const fileInput  = document.getElementById("imageUpload");
  const statusText = document.getElementById("uploadStatus");
  const resultImg  = document.getElementById("uploadedResult");

  if (!fileInput.files.length) {
    statusText.textContent = "⚠️ Please select an image first.";
    return;
  }

  const formData = new FormData();
  formData.append("image", fileInput.files[0]);

  statusText.textContent = "⏳ Analysing image...";

  fetch("/upload", {
    method: "POST",
    body: formData
  })
  .then(res => res.json())
  .then(data => {
    if (data.error) {
      statusText.textContent = "❌ Error: " + data.error;
      return;
    }

    // Update the dashboard stats with results from uploaded image
    document.getElementById("total").textContent    = data.total_chairs;
    document.getElementById("free").textContent     = data.free;
    document.getElementById("occupied").textContent = data.occupied;
    document.getElementById("percent").textContent  = data.occupancy_percent + "%";
    document.getElementById("progressBar").style.width = data.occupancy_percent + "%";

    statusText.textContent =
      `✅ Done! Free: ${data.free} | Occupied: ${data.occupied} | Total: ${data.total_chairs}`;

    // Show the annotated result image
    resultImg.src     = "/snapshot?t=" + new Date().getTime();
    resultImg.style.display = "block";
  })
  .catch(err => {
    statusText.textContent = "❌ Failed to analyse. Try again.";
    console.error(err);
  });
}
