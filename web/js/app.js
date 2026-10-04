/**
 * Kanpur LST & Microclimate GIS Portal
 * Master Interactive Logic: Leaflet Vector GIS, Chart.js Telemetry Engine,
 * Dynamic Map Inspector, Lightbox Gallery & Microclimate Simulator
 */

// Global State
let rawTelemetry = [];
let filteredTelemetry = [];
let telemetryChart = null;
let currentTab = 'tabTimeline';

let map = null;
let tileLayers = {};
let geoJsonLayers = {
  zones: null,
  stations: null,
  ganga: null,
  transect: null
};

// Zone Metadata for Simulator & Inspector
const ZONE_METADATA = {
  "ZONE_01": {
    name: "Central Kanpur Urban Core",
    uhi: +2.1,
    albedo: "10–12%",
    type: "High-Density Commercial & Masonry",
    area: "24.5 km²",
    pop: "850,000",
    mitigation: "Install high-albedo cool roofs and green rooftop canopies to lower nocturnal heat retention by ~1.2°C."
  },
  "ZONE_02": {
    name: "Jajmau Industrial Tannery Cluster",
    uhi: +1.8,
    albedo: "13–15%",
    type: "Heavy Industrial & Worker Settlements",
    area: "21.8 km²",
    pop: "320,000",
    mitigation: "Establish perimeter vegetative shelterbelts and waste heat recovery on tannery boiler stacks."
  },
  "ZONE_03": {
    name: "Panki Industrial & Thermal Buffer",
    uhi: +1.6,
    albedo: "12–14%",
    type: "Thermal Power & Heavy Fabrication",
    area: "19.4 km²",
    pop: "140,000",
    mitigation: "Phased fly ash pond re-vegetation and solar reflective industrial roof coatings."
  },
  "ZONE_04": {
    name: "IITK & Kalyanpur Institutional Belt",
    uhi: -0.8,
    albedo: "22–26%",
    type: "Institutional Campus / Urban Forest",
    area: "28.2 km²",
    pop: "65,000",
    mitigation: "Preserve continuous ecological canopy; serves as a critical biological cooling buffer for northwest Kanpur."
  },
  "ZONE_05": {
    name: "Ganga Riparian Buffer & Floodplain",
    uhi: -2.4,
    albedo: "25–30%",
    type: "Alluvial Floodplain & Active Channel",
    area: "36.0 km²",
    pop: "15,000",
    mitigation: "Strict moratorium on floodplain paving and encroachment to preserve regional nocturnal convective drainage."
  }
};

// Document Ready
document.addEventListener('DOMContentLoaded', async () => {
  initThemeToggle();
  initLeafletMap();
  initSimulator();
  initGalleryFilters();
  initLightbox();
  initChartTabs();
  initFilterListeners();
  initQuickJumps();

  await loadTelemetryData();
  await loadGeoJsonLayers();
  renderChart();
});

/* --------------------------------------------------------------------------
   Theme Toggle
   -------------------------------------------------------------------------- */
function initThemeToggle() {
  const btn = document.getElementById('themeToggleBtn');
  const savedTheme = localStorage.getItem('kanpur_lst_theme') || 'dark';
  if (savedTheme === 'light') {
    document.body.classList.remove('dark-theme');
    document.body.classList.add('light-theme');
    btn.innerHTML = '<i class="fa-solid fa-sun"></i>';
  }

  btn.addEventListener('click', () => {
    if (document.body.classList.contains('dark-theme')) {
      document.body.classList.remove('dark-theme');
      document.body.classList.add('light-theme');
      btn.innerHTML = '<i class="fa-solid fa-sun"></i>';
      localStorage.setItem('kanpur_lst_theme', 'light');
    } else {
      document.body.classList.remove('light-theme');
      document.body.classList.add('dark-theme');
      btn.innerHTML = '<i class="fa-solid fa-moon"></i>';
      localStorage.setItem('kanpur_lst_theme', 'dark');
    }
  });
}

/* --------------------------------------------------------------------------
   Quick Event Jumps
   -------------------------------------------------------------------------- */
function initQuickJumps() {
  const pills = document.querySelectorAll('.event-pill');
  pills.forEach(pill => {
    pill.addEventListener('click', () => {
      const year = pill.getAttribute('data-year');
      const season = pill.getAttribute('data-season');
      document.getElementById('yearFilter').value = year;
      document.getElementById('seasonFilter').value = season;
      applyFilters();
      renderChart();
    });
  });
}

/* --------------------------------------------------------------------------
   Leaflet GIS Map
   -------------------------------------------------------------------------- */
function initLeafletMap() {
  const kanpurCenter = [26.465, 80.325];
  map = L.map('leafletMap', {
    center: kanpurCenter,
    zoom: 11,
    zoomControl: true,
    attributionControl: false
  });

  // Base Tile Layers
  tileLayers.dark = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    maxZoom: 19
  });
  tileLayers.satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 18
  });
  tileLayers.osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19
  });

  tileLayers.dark.addTo(map);

  // Basemap Selector
  const basemapSelect = document.getElementById('basemapSelect');
  basemapSelect.addEventListener('change', (e) => {
    Object.values(tileLayers).forEach(layer => map.removeLayer(layer));
    const selected = e.target.value;
    if (tileLayers[selected]) {
      tileLayers[selected].addTo(map);
    }
  });

  // Reset View
  document.getElementById('resetMapViewBtn').addEventListener('click', () => {
    map.setView(kanpurCenter, 11, { animate: true });
  });

  // Layer Toggles
  document.getElementById('layerZonesToggle').addEventListener('change', (e) => {
    if (geoJsonLayers.zones) {
      if (e.target.checked) map.addLayer(geoJsonLayers.zones);
      else map.removeLayer(geoJsonLayers.zones);
    }
  });
  document.getElementById('layerStationsToggle').addEventListener('change', (e) => {
    if (geoJsonLayers.stations) {
      if (e.target.checked) map.addLayer(geoJsonLayers.stations);
      else map.removeLayer(geoJsonLayers.stations);
    }
  });
  document.getElementById('layerGangaToggle').addEventListener('change', (e) => {
    if (geoJsonLayers.ganga) {
      if (e.target.checked) map.addLayer(geoJsonLayers.ganga);
      else map.removeLayer(geoJsonLayers.ganga);
    }
  });
  document.getElementById('layerTransectToggle').addEventListener('change', (e) => {
    if (geoJsonLayers.transect) {
      if (e.target.checked) map.addLayer(geoJsonLayers.transect);
      else map.removeLayer(geoJsonLayers.transect);
    }
  });
}

function updateInspector(type, name, uhi, morphology, albedo, area, mitigation) {
  document.getElementById('inspectorTag').innerText = type.toUpperCase();
  document.getElementById('inspectorName').innerText = name;
  document.getElementById('inspectorUHI').innerText = (uhi > 0 ? '+' : '') + uhi + '°C';
  document.getElementById('inspectorUHI').className = 'cell-val ' + (uhi >= 0 ? 'text-red' : 'text-cyan');
  document.getElementById('inspectorType').innerText = morphology;
  document.getElementById('inspectorAlbedo').innerText = albedo;
  document.getElementById('inspectorArea').innerText = area;
  document.getElementById('inspectorMitigation').innerHTML = `<strong>Mitigation Strategy:</strong> ${mitigation}`;
}

async function loadGeoJsonLayers() {
  const zoneColors = {
    "ZONE_01": "#EF4444",
    "ZONE_02": "#DC2626",
    "ZONE_03": "#F97316",
    "ZONE_04": "#10B981",
    "ZONE_05": "#06B6D4"
  };

  try {
    // 1. Thermal Zones
    const resZones = await fetch('data/kanpur_thermal_zones.geojson');
    const zonesData = await resZones.json();
    geoJsonLayers.zones = L.geoJSON(zonesData, {
      style: (feat) => {
        const zid = feat.properties.zone_id;
        const col = zoneColors[zid] || '#EF4444';
        return {
          color: col,
          fillColor: col,
          fillOpacity: 0.35,
          weight: 2,
          opacity: 0.9
        };
      },
      onEachFeature: (feat, layer) => {
        const p = feat.properties;
        const popContent = `
          <div style="font-family:'Plus Jakarta Sans',sans-serif; min-width:210px;">
            <div style="font-size:0.72rem;font-weight:700;color:#94a3b8;text-transform:uppercase;">${p.zone_id}</div>
            <div style="font-size:0.95rem;font-weight:800;margin-bottom:0.4rem;color:#1e293b;">${p.name}</div>
            <div style="font-size:0.8rem;margin-bottom:0.2rem;"><strong>Modeled UHI:</strong> <span style="color:${p.mean_uhi_offset_c >= 0 ? '#dc2626':'#0284c7'};font-weight:700;">${p.mean_uhi_offset_c > 0 ? '+' : ''}${p.mean_uhi_offset_c}°C</span></div>
            <div style="font-size:0.75rem;color:#475569;margin-bottom:0.2rem;"><strong>Land Cover:</strong> ${p.classification}</div>
            <div style="font-size:0.75rem;color:#475569;margin-bottom:0.2rem;"><strong>Albedo:</strong> ${p.albedo_characteristic}</div>
            <div style="font-size:0.75rem;color:#475569;margin-bottom:0.4rem;"><strong>Area:</strong> ${p.area_sqkm} km² | <strong>Pop:</strong> ~${p.estimated_population?.toLocaleString()}</div>
            <div style="font-size:0.72rem;background:#f1f5f9;padding:0.35rem;border-radius:4px;border-left:3px solid #3b82f6;"><strong>Mitigation:</strong> ${p.cooling_mitigation_priority}</div>
          </div>
        `;
        layer.bindPopup(popContent);
        layer.on('mouseover', () => layer.setStyle({ fillOpacity: 0.65, weight: 3 }));
        layer.on('mouseout', () => layer.setStyle({ fillOpacity: 0.35, weight: 2 }));
        layer.on('click', () => {
          updateInspector(
            "Thermal Microclimate Zone",
            p.name,
            p.mean_uhi_offset_c,
            p.classification,
            p.albedo_characteristic,
            p.area_sqkm + " km²",
            p.cooling_mitigation_priority
          );
        });
      }
    }).addTo(map);

    // 2. CPCB Stations
    const resStations = await fetch('data/kanpur_cpcb_stations.geojson');
    const stationsData = await resStations.json();
    geoJsonLayers.stations = L.geoJSON(stationsData, {
      pointToLayer: (feat, latlng) => {
        return L.circleMarker(latlng, {
          radius: 9,
          fillColor: '#4338CA',
          color: '#ffffff',
          weight: 2.5,
          opacity: 1,
          fillOpacity: 0.95
        });
      },
      onEachFeature: (feat, layer) => {
        const p = feat.properties;
        const popContent = `
          <div style="font-family:'Plus Jakarta Sans',sans-serif; min-width:210px;">
            <div style="font-size:0.72rem;font-weight:700;color:#6366f1;">CAAQMS STATION #${p.station_id}</div>
            <div style="font-size:0.95rem;font-weight:800;color:#1e1b4b;margin-bottom:0.3rem;">${p.name}</div>
            <div style="font-size:0.78rem;color:#334155;margin-bottom:0.2rem;"><strong>Operator:</strong> ${p.operator}</div>
            <div style="font-size:0.78rem;color:#334155;margin-bottom:0.2rem;"><strong>Setting:</strong> ${p.zone}</div>
            <div style="font-size:0.78rem;color:#334155;margin-bottom:0.2rem;"><strong>Elevation:</strong> ${p.elevation_m} m ASL</div>
            <div style="font-size:0.78rem;color:#dc2626;margin-bottom:0.2rem;"><strong>Mean Winter PM2.5:</strong> ${p.mean_winter_pm25_ugm3} µg/m³</div>
            <div style="font-size:0.75rem;background:#eef2ff;color:#312e81;padding:0.35rem;border-radius:4px;"><strong>Inversion Vulnerability:</strong> ${p.inversion_vulnerability}</div>
          </div>
        `;
        layer.bindPopup(popContent);
        layer.on('click', () => {
          updateInspector(
            "CAAQMS Ground Station",
            `${p.name} (UPPCB / CPCB)`,
            0.0,
            p.zone,
            "Urban Concrete",
            `Elevation: ${p.elevation_m}m`,
            `Winter PM2.5 Inversion Vulnerability: ${p.inversion_vulnerability}. Dominant source: ${p.dominant_source}.`
          );
        });
      }
    }).addTo(map);

    // 3. Ganga Riparian Corridor
    const resGanga = await fetch('data/kanpur_ganga_riparian.geojson');
    const gangaData = await resGanga.json();
    geoJsonLayers.ganga = L.geoJSON(gangaData, {
      style: {
        color: '#0284C7',
        weight: 5,
        opacity: 0.75
      },
      onEachFeature: (feat, layer) => {
        layer.bindPopup(`<strong>Ganga River Hydrographic Corridor</strong><br>Active Evaporative Cooling Sink (-2.4°C)`);
      }
    }).addTo(map);

    // 4. Transect Line
    const resTransect = await fetch('data/kanpur_microclimate_transect.geojson');
    const transectData = await resTransect.json();
    geoJsonLayers.transect = L.geoJSON(transectData, {
      style: {
        color: '#94A3B8',
        weight: 2.5,
        dashArray: '6, 6',
        opacity: 0.85
      },
      onEachFeature: (feat, layer) => {
        layer.bindPopup(`<strong>25-km West-East Diagnostic Transect</strong><br>Panki &rarr; IITK &rarr; Central Core &rarr; Jajmau &rarr; Ganga`);
      }
    }).addTo(map);

  } catch (err) {
    console.warn("Could not fetch remote GeoJSON:", err);
  }
}

/* --------------------------------------------------------------------------
   Telemetry Data Ingestion & Filtering
   -------------------------------------------------------------------------- */
async function loadTelemetryData() {
  try {
    const res = await fetch('data/kanpur_lst_daily.json');
    rawTelemetry = await res.json();
    document.getElementById('telemetryCountBadge').innerText = `${rawTelemetry.length.toLocaleString()} Daily Observations`;
    applyFilters();
  } catch (err) {
    console.warn("Failed to load kanpur_lst_daily.json, using fallback:", err);
    rawTelemetry = generateSyntheticTelemetry();
    applyFilters();
  }
}

function initFilterListeners() {
  document.getElementById('yearFilter').addEventListener('change', () => {
    applyFilters();
    renderChart();
  });
  document.getElementById('seasonFilter').addEventListener('change', () => {
    applyFilters();
    renderChart();
  });
}

function applyFilters() {
  const year = document.getElementById('yearFilter').value;
  const season = document.getElementById('seasonFilter').value;

  filteredTelemetry = rawTelemetry.filter(d => {
    const matchYear = (year === 'ALL' || d.year === parseInt(year));
    const matchSeason = (season === 'ALL' || d.season === season);
    return matchYear && matchSeason;
  });

  updateDiagnosticInsights();
}

function initChartTabs() {
  const tabs = document.querySelectorAll('.tab-btn');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentTab = tab.getAttribute('data-tab');
      renderChart();
      updateDiagnosticInsights();
    });
  });
}

/* --------------------------------------------------------------------------
   Chart.js Telemetry Engine (5 Modes)
   -------------------------------------------------------------------------- */
function renderChart() {
  const ctx = document.getElementById('telemetryChart').getContext('2d');
  if (telemetryChart) {
    telemetryChart.destroy();
  }

  // Downsample if more than 500 records for smooth 60fps rendering
  const step = Math.max(1, Math.floor(filteredTelemetry.length / 365));
  const dataSubset = filteredTelemetry.filter((_, i) => i % step === 0);
  const labels = dataSubset.map(d => d.date);

  let chartConfig = {};

  if (currentTab === 'tabTimeline') {
    // Mode 1: LST vs Air Temp
    chartConfig = {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Land Surface Temp (LST / Skin °C)',
            data: dataSubset.map(d => d.lst),
            borderColor: '#F59E0B',
            backgroundColor: 'rgba(245, 158, 11, 0.1)',
            borderWidth: 1.8,
            pointRadius: 0,
            tension: 0.2
          },
          {
            label: '2m Ambient Air Temp (°C)',
            data: dataSubset.map(d => d.air_t),
            borderColor: '#3B82F6',
            borderWidth: 1.5,
            borderDash: [4, 4],
            pointRadius: 0,
            tension: 0.2
          }
        ]
      },
      options: getCommonChartOptions("Temperature (°C)", 0, 50)
    };
  } else if (currentTab === 'tabGradient') {
    // Mode 2: Delta T (Skin - Air)
    chartConfig = {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Thermal Gradient ΔT (Tskin - Tair, °C)',
            data: dataSubset.map(d => d.delta_t),
            backgroundColor: dataSubset.map(d => (d.delta_t >= 0 ? 'rgba(239, 68, 68, 0.75)' : 'rgba(59, 130, 246, 0.75)')),
            borderWidth: 0
          }
        ]
      },
      options: getCommonChartOptions("Thermal Gradient ΔT (°C)", -5, 5)
    };
  } else if (currentTab === 'tabPM25') {
    // Mode 3: Ground PM2.5 vs Satellite LST & Inversion
    chartConfig = {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Ground CAAQMS PM2.5 (µg/m³)',
            data: dataSubset.map(d => d.pm25),
            borderColor: '#DC2626',
            backgroundColor: 'rgba(220, 38, 38, 0.15)',
            borderWidth: 2,
            pointRadius: 1,
            yAxisID: 'y1'
          },
          {
            label: 'Satellite Skin Temp LST (°C)',
            data: dataSubset.map(d => d.lst),
            borderColor: '#F59E0B',
            borderWidth: 1.5,
            pointRadius: 0,
            yAxisID: 'y2'
          },
          {
            label: 'NAAQS Standard (60 µg/m³)',
            data: labels.map(() => 60),
            borderColor: '#EF4444',
            borderDash: [5, 5],
            borderWidth: 1.2,
            pointRadius: 0,
            yAxisID: 'y1'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { labels: { color: '#94a3b8', font: { family: 'Plus Jakarta Sans', size: 11 } } },
          tooltip: { backgroundColor: 'rgba(15, 23, 42, 0.95)' }
        },
        scales: {
          x: { ticks: { color: '#64748b', maxTicksLimit: 10 }, grid: { display: false } },
          y1: {
            type: 'linear',
            position: 'left',
            title: { display: true, text: 'PM2.5 (µg/m³)', color: '#DC2626' },
            ticks: { color: '#64748b' },
            grid: { color: 'rgba(255, 255, 255, 0.05)' }
          },
          y2: {
            type: 'linear',
            position: 'right',
            title: { display: true, text: 'LST (°C)', color: '#F59E0B' },
            ticks: { color: '#64748b' },
            grid: { display: false }
          }
        }
      }
    };
  } else if (currentTab === 'tabInversion') {
    // Mode 4: Ventilation Coeff & NISI
    chartConfig = {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Ventilation Coeff Vc (m²/s)',
            data: dataSubset.map(d => d.vc),
            borderColor: '#2563EB',
            borderWidth: 1.8,
            pointRadius: 0,
            yAxisID: 'y1'
          },
          {
            label: 'Nocturnal Inversion Severity Index (NISI)',
            data: dataSubset.map(d => d.nisi),
            borderColor: '#D97706',
            backgroundColor: 'rgba(217, 119, 6, 0.15)',
            borderWidth: 2,
            pointRadius: 0,
            yAxisID: 'y2'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { labels: { color: '#94a3b8', font: { family: 'Plus Jakarta Sans', size: 11 } } },
          tooltip: { backgroundColor: 'rgba(15, 23, 42, 0.95)' }
        },
        scales: {
          x: { ticks: { color: '#64748b', maxTicksLimit: 10 }, grid: { display: false } },
          y1: {
            type: 'linear',
            position: 'left',
            title: { display: true, text: 'Vc (m²/s)', color: '#2563EB' },
            ticks: { color: '#64748b' },
            grid: { color: 'rgba(255, 255, 255, 0.05)' }
          },
          y2: {
            type: 'linear',
            position: 'right',
            title: { display: true, text: 'NISI Score', color: '#D97706' },
            ticks: { color: '#64748b' },
            grid: { display: false }
          }
        }
      }
    };
  } else if (currentTab === 'tabHeatIndex') {
    // Mode 5: Bioclimatic Heat Index
    chartConfig = {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'NOAA Heat Index (Apparent °C)',
            data: dataSubset.map(d => d.heat_idx),
            borderColor: '#EF4444',
            backgroundColor: 'rgba(239, 68, 68, 0.15)',
            borderWidth: 2,
            pointRadius: 0
          },
          {
            label: 'Danger Threshold (41°C)',
            data: labels.map(() => 41),
            borderColor: '#DC2626',
            borderDash: [6, 4],
            borderWidth: 1.5,
            pointRadius: 0
          }
        ]
      },
      options: getCommonChartOptions("Heat Index / Apparent Temp (°C)", 15, 55)
    };
  }

  telemetryChart = new Chart(ctx, chartConfig);
}

function getCommonChartOptions(yTitle, yMin, yMax) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: {
        position: 'top',
        labels: { color: '#94a3b8', font: { family: 'Plus Jakarta Sans', size: 11 } }
      },
      tooltip: { backgroundColor: 'rgba(15, 23, 42, 0.95)', titleColor: '#f8fafc', bodyColor: '#cbd5e1' }
    },
    scales: {
      x: { ticks: { color: '#64748b', maxTicksLimit: 10 }, grid: { display: false } },
      y: {
        min: yMin,
        max: yMax,
        title: { display: true, text: yTitle, color: '#94a3b8' },
        ticks: { color: '#64748b' },
        grid: { color: 'rgba(255, 255, 255, 0.05)' }
      }
    }
  };
}

function updateDiagnosticInsights() {
  const textEl = document.getElementById('diagnosticText');
  const count = filteredTelemetry.length;

  if (count === 0) {
    textEl.innerHTML = "No observations match the selected year and season filter.";
    return;
  }

  const meanLST = (filteredTelemetry.reduce((acc, d) => acc + (d.lst || 0), 0) / count).toFixed(1);
  const meanAir = (filteredTelemetry.reduce((acc, d) => acc + (d.air_t || 0), 0) / count).toFixed(1);
  const meanDelta = (filteredTelemetry.reduce((acc, d) => acc + (d.delta_t || 0), 0) / count).toFixed(2);
  const severeInversionCount = filteredTelemetry.filter(d => (d.nisi || 0) > 1.8).length;
  const dangerHeatCount = filteredTelemetry.filter(d => (d.heat_idx || 0) >= 41.0).length;

  if (currentTab === 'tabTimeline') {
    textEl.innerHTML = `Analyzing <strong>${count.toLocaleString()} daily records</strong>. Mean LST: <strong>${meanLST}°C</strong> vs Mean Air: <strong>${meanAir}°C</strong>. Summer solar insolation drives skin superheating up to +3.3°C above ambient air.`;
  } else if (currentTab === 'tabGradient') {
    textEl.innerHTML = `Mean Thermal Gradient (&Delta;T): <strong>${meanDelta > 0 ? '+' : ''}${meanDelta}°C</strong>. Negative &Delta;T values mark nocturnal infrared radiation chill capping the boundary layer.`;
  } else if (currentTab === 'tabPM25') {
    textEl.innerHTML = `Coupled Satellite LST with Ground CAAQMS Particulates: Winter nocturnal radiational chilling collapses the boundary layer below 250m, driving ground $\\text{PM}_{2.5}$ beyond 250 µg/m³.`;
  } else if (currentTab === 'tabInversion') {
    textEl.innerHTML = `Identified <strong>${severeInversionCount} severe inversion days (NISI &gt; 1.8)</strong>. Boundary layer ventilation drops below 2,000 m²/s during these episodes, locking in fine particulates.`;
  } else if (currentTab === 'tabHeatIndex') {
    textEl.innerHTML = `Recorded <strong>${dangerHeatCount} dangerous bioclimatic heat stress days (HI &ge; 41°C)</strong> where combined temperature and humidity present severe hyperthermia risk.`;
  }
}

/* --------------------------------------------------------------------------
   Zone Comparison Simulator
   -------------------------------------------------------------------------- */
function initSimulator() {
  const selA = document.getElementById('zoneSelectA');
  const selB = document.getElementById('zoneSelectB');

  function updateSimulator() {
    const zA = ZONE_METADATA[selA.value];
    const zB = ZONE_METADATA[selB.value];
    const diff = (zA.uhi - zB.uhi).toFixed(1);
    const grid = document.getElementById('simResultsGrid');

    grid.innerHTML = `
      <div class="sim-metric-card">
        <span class="sim-metric-title">UHI Thermal Differential</span>
        <span class="sim-metric-val ${diff > 0 ? 'text-red':'text-blue'}">${diff > 0 ? '+' : ''}${diff}°C</span>
        <span class="sim-metric-desc">${zA.name} is ${Math.abs(diff)}°C ${diff > 0 ? 'warmer':'cooler'} than ${zB.name}.</span>
      </div>
      <div class="sim-metric-card">
        <span class="sim-metric-title">Albedo Contrast</span>
        <span class="sim-metric-val text-amber">${zA.albedo.split(' ')[0]} vs ${zB.albedo.split(' ')[0]}</span>
        <span class="sim-metric-desc">Disparity in solar reflectance and thermal inertia.</span>
      </div>
      <div class="sim-metric-card">
        <span class="sim-metric-title">Exposed Population</span>
        <span class="sim-metric-val text-purple">${zA.pop} vs ${zB.pop}</span>
        <span class="sim-metric-desc">Comparative human exposure in metropolitan basin.</span>
      </div>
      <div class="sim-metric-card">
        <span class="sim-metric-title">Key Policy Recommendation</span>
        <span class="sim-metric-desc" style="color:var(--text-main); font-weight:500;">${zA.mitigation}</span>
      </div>
    `;
  }

  selA.addEventListener('change', updateSimulator);
  selB.addEventListener('change', updateSimulator);
  updateSimulator();
}

/* --------------------------------------------------------------------------
   Gallery Filters & Lightbox
   -------------------------------------------------------------------------- */
function initGalleryFilters() {
  const filterBtns = document.querySelectorAll('.gallery-filter');
  const figureCards = document.querySelectorAll('.figure-card');

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const cat = btn.getAttribute('data-fig');

      figureCards.forEach(card => {
        if (cat === 'all' || card.getAttribute('data-category') === cat) {
          card.style.display = 'flex';
        } else {
          card.style.display = 'none';
        }
      });
    });
  });
}

function initLightbox() {
  const modal = document.getElementById('figureLightbox');
  const backdrop = document.getElementById('lightboxBackdrop');
  const closeBtn = document.getElementById('lightboxCloseBtn');
  const imgEl = document.getElementById('lightboxImg');
  const titleEl = document.getElementById('lightboxTitle');
  const dlBtn = document.getElementById('lightboxDownloadBtn');

  function openLightbox(src, title) {
    imgEl.src = src;
    titleEl.innerText = title;
    dlBtn.href = src;
    modal.classList.add('active');
  }

  function closeLightbox() {
    modal.classList.remove('active');
  }

  document.querySelectorAll('.fig-expand-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      openLightbox(btn.getAttribute('data-img'), btn.getAttribute('data-title'));
    });
  });

  backdrop.addEventListener('click', closeLightbox);
  closeBtn.addEventListener('click', closeLightbox);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeLightbox();
  });
}

/* --------------------------------------------------------------------------
   Synthetic Telemetry Generator (Offline Fallback)
   -------------------------------------------------------------------------- */
function generateSyntheticTelemetry() {
  const records = [];
  const startDate = new Date(2017, 0, 1);
  for (let i = 0; i < 2556; i++) {
    const cur = new Date(startDate);
    cur.setDate(startDate.getDate() + i);
    const m = cur.getMonth() + 1;
    const y = cur.getFullYear();

    let season = "Post-Monsoon";
    if ([12, 1, 2].includes(m)) season = "Winter";
    else if ([3, 4, 5].includes(m)) season = "Summer";
    else if ([6, 7, 8, 9].includes(m)) season = "Monsoon";

    const doy = i % 365;
    const tempAir = 25.0 + 12.0 * Math.sin((doy - 100) * 2 * Math.PI / 365) + (Math.random() * 4 - 2);
    const deltaT = (season === 'Summer') ? (Math.random() * 2.5 + 0.5) : (season === 'Winter' ? -(Math.random() * 2.5 + 0.5) : (Math.random() * 1.5 - 0.5));
    const tempSkin = tempAir + deltaT;
    const rh = (season === 'Monsoon') ? (75 + Math.random() * 20) : (45 + Math.random() * 30);
    const ws = 1.5 + Math.random() * 2.5;
    const heatIdx = (tempAir >= 25) ? (tempAir + (rh / 100) * 8) : tempAir;
    const nisi = (deltaT < 0) ? (Math.abs(deltaT) * (1 + rh / 100) / Math.max(1, ws)) : 0;
    const vc = (deltaT < 0) ? (ws * 300) : (ws * 1500);
    const pm25 = (deltaT < 0) ? (140 + Math.random() * 140) : (35 + Math.random() * 40);

    records.push({
      date: cur.toISOString().split('T')[0],
      year: y,
      month: m,
      season: season,
      lst: parseFloat(tempSkin.toFixed(1)),
      air_t: parseFloat(tempAir.toFixed(1)),
      delta_t: parseFloat(deltaT.toFixed(1)),
      heat_idx: parseFloat(heatIdx.toFixed(1)),
      nisi: parseFloat(nisi.toFixed(2)),
      vc: parseFloat(vc.toFixed(0)),
      pm25: parseFloat(pm25.toFixed(1)),
      rh: parseFloat(rh.toFixed(1)),
      ws: parseFloat(ws.toFixed(1))
    });
  }
  return records;
}
