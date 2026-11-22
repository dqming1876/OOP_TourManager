// The bundled catalog remains a read-only fallback when the API is unavailable.
let destinationEntries = [];
async function refreshDestinations() {
  const response = await fetch("/api/ops/destinations", { cache: "no-store" });
  if (!response.ok) throw new Error("Không tải được danh mục dùng chung.");
  const { entries } = await response.json();
  for (const province of PROVINCES) {
    for (const kind of ["attractions", "specialties"]) {
      province[kind] = entries
        .filter((row) => row.province_id === province.id && row.kind === kind)
        .map((row) => row.name);
    }
  }
  for (const entry of entries) {
    IMAGE_MAP[entry.name] = {
      ...IMAGE_MAP[entry.name],
      url: entry.url,
      source: entry.source,
      description: entry.description,
    };
  }
  destinationEntries = entries;
}
async function loadSharedDestinations() {
  try {
    await refreshDestinations();
    const page = location.hash.split("/")[0];
    if (["#places", "#province", "#tour", "#home", ""].includes(page)) render();
    if (
      page === "#admin" &&
      typeof adminTab !== "undefined" &&
      adminTab === "destinations"
    ) {
      const selected = document.querySelector("#edit-province")?.value;
      if (selected) destinationEditor(selected);
    }
  } catch (error) {
    console.warn(error.message);
  }
}
window.addEventListener("hashchange", loadSharedDestinations);
window.addEventListener("focus", loadSharedDestinations);
loadSharedDestinations();
