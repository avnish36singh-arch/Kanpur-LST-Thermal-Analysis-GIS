# Kanpur Land Surface Temperature (LST) & Urban Inversion Dynamics

**Satellite Earth Observation, MERRA-2 Reanalysis, and QGIS Microclimate Spatial Modeling (2017–2023)**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Data: NASA POWER](https://img.shields.io/badge/Data-NASA%20POWER%20MERRA--2-orange.svg)](https://power.larc.nasa.gov/)
[![GIS: QGIS 3.x](https://img.shields.io/badge/GIS-QGIS%20Vector%20EPSG%3A4326-darkgreen.svg)](https://qgis.org)
[![Part of Signal Earth](https://img.shields.io/badge/Platform-Signal%20Earth-cyan.svg)](https://github.com/avnish36singh-arch/delhi-air_qaulity_cpcb)

> **Dedicated Remote Sensing & GIS Repository**  
> • **Domain**: Kanpur Metropolitan Basin ($26.4499^\circ\text{N}, 80.3319^\circ\text{E}$), Indo-Gangetic Plain, Uttar Pradesh, India  
> • **Sibling Station Repo**: [Air-Quality-Analysis-Kanpur](https://github.com/avnish36singh-arch/Air-Quality-Analysis-Kanpur)  
> • **Sibling Delhi Repo**: [delhi-air_qaulity_cpcb](https://github.com/avnish36singh-arch/delhi-air_qaulity_cpcb)  
> • **Web Portal**: Published on [Signal Earth](https://github.com/avnish36singh-arch/delhi-air_qaulity_cpcb/tree/main/web)

---

## Abstract

This repository provides an autonomous, reproducible remote sensing and geospatial analytics pipeline investigating multi-year **Land Surface Temperature (LST)**, radiant skin-to-air thermal decoupling, and urban heat island (UHI) microclimate gradients across Kanpur, Uttar Pradesh.

Covering **2,556 consecutive daily observations (2017–2023)** retrieved from the **NASA POWER API (MERRA-2 assimilation reanalysis)** and coupled with **QGIS 3.x vector spatial microclimate layers**, the project investigates the thermodynamic mechanisms governing nocturnal boundary layer collapse and particulate trapping in the central Indo-Gangetic Plain.

---

## Key Scientific Findings

- **Seven-Year Continuous Climatology**: 2,556 unbroken daily records. Mean LST: **$25.96^\circ\text{C}$**, Mean Air Temp: **$25.87^\circ\text{C}$**. Peak summer skin temperature: **$43.39^\circ\text{C}$** (June 12, 2019); winter minimum: **$5.61^\circ\text{C}$** (December 30, 2019).
- **Summer Solar Superheating ($\Delta T > 0$)**: In pre-monsoon summer (April–June), radiant skin temperature exceeds ambient air temperature by a mean of **$+1.01^\circ\text{C}$** (peaking at $+3.25^\circ\text{C}$), generating intense convective thermal mixing.
- **Winter Radiation Inversion ($\Delta T < 0$)**: In post-monsoon and winter (November–February), rapid nocturnal infrared radiation loss drops skin temperatures **$-0.97^\circ\text{C}$** below overlying air, capping the boundary layer under 250 m and trapping ground-level $\text{PM}_{2.5}$.
- **Spatial Microclimate Heterogeneity (QGIS Modeling)**:
  - Central Urban Core: **$+2.1^\circ\text{C}$** UHI offset
  - Jajmau Tannery Belt: **$+1.8^\circ\text{C}$** UHI offset
  - Panki Industrial Zone: **$+1.6^\circ\text{C}$** UHI offset
  - IIT Kanpur Green Canopy: **$-0.8^\circ\text{C}$** vegetative cooling buffer
  - Ganga Riparian Floodplain: **$-2.4^\circ\text{C}$** evaporative cooling sink

---

## Publication Figures

### Figure 1: Seven-Year Multi-Year LST Climatology & Thermal Stress
![Figure 1: LST Seasonal Timeline](outputs/plots/01_kanpur_lst_seasonal_timeline.png)
*Figure 1: Seven-year continuous trajectory of daily radiant skin temperature (LST) and 2m ambient air temperature with 7-day rolling trends and thermal stress classification bands.*

---

### Figure 2: Monthly Thermal Gradient ($\Delta T = T_{\text{skin}} - T_{\text{air}}$)
![Figure 2: Thermal Gradient Boxplots](outputs/plots/02_skin_vs_air_temperature_anomaly.png)
*Figure 2: Monthly distribution of the thermal gradient ($\Delta T$), illustrating the switch from summer solar superheating (April–June, $\Delta T > 0$) to winter nocturnal radiative cooling (November–February, $\Delta T < 0$).*

---

### Figure 3: Spatial Microclimate GIS Map & CPCB Station Overlay
![Figure 3: Kanpur Spatial Thermal Zones](outputs/plots/03_kanpur_spatial_thermal_zones.png)
*Figure 3: Spatial vector GIS map modeled in QGIS 3.x (EPSG:4326), mapping urban core UHI, industrial corridors, IITK canopy cooling, and the Ganga floodplain buffer alongside UPPCB CAAQMS monitoring stations.*

---

### Figure 4: Satellite Surface Cooling vs Ground CAAQMS $\text{PM}_{2.5}$ Inversion Spikes
![Figure 4: Inversion Coupling](outputs/plots/04_lst_inversion_coupling_pm25.png)
*Figure 4: Direct multi-panel thermodynamic coupling: satellite radiant skin temperature (Panel 1), inversion thermal gradient (Panel 2), and ground CAAQMS $\text{PM}_{2.5}$ winter entrapment spikes (Panel 3).*

---

## QGIS Spatial Vector Layers

Standardized GeoJSON layers in `outputs/qgis/` (EPSG:4326 WGS84) ready for drag-and-drop analysis in QGIS or ArcGIS:
1. `outputs/qgis/kanpur_thermal_zones.geojson`: Polygons covering Central Core, Jajmau, Panki, IITK, and Ganga Wetland with modeled UHI offset attributes.
2. `outputs/qgis/kanpur_cpcb_stations.geojson`: Point features for CPCB/UPPCB CAAQMS stations at NSI Kalyanpur and Nehru Nagar.

---

## Pipeline Execution

### 1. Installation
```bash
git clone https://github.com/avnish36singh-arch/Kanpur-LST-Thermal-Analysis-GIS.git
cd Kanpur-LST-Thermal-Analysis-GIS
pip install -r requirements.txt
```

### 2. Fetch Fresh NASA POWER Satellite Telemetry
```bash
python pipeline/fetch_nasa_power.py
```

### 3. Generate QGIS Vector Layers & Publication Figures
```bash
python pipeline/spatial_kanpur_gis.py
```

---

## Directory Manifest

```
Kanpur-LST-Thermal-Analysis-GIS/
├── data/
│   └── raw/
│       └── kanpur_nasa_power_daily.csv       # 2,556 daily observations (2017-2023)
├── outputs/
│   ├── plots/                                # 300-DPI publication figures
│   │   ├── 01_kanpur_lst_seasonal_timeline.png
│   │   ├── 02_skin_vs_air_temperature_anomaly.png
│   │   ├── 03_kanpur_spatial_thermal_zones.png
│   │   └── 04_lst_inversion_coupling_pm25.png
│   └── qgis/                                 # QGIS vector spatial layers
│       ├── kanpur_thermal_zones.geojson
│       └── kanpur_cpcb_stations.geojson
├── pipeline/
│   ├── fetch_nasa_power.py                   # NASA POWER REST API telemetry ingestion
│   └── spatial_kanpur_gis.py                 # QGIS vector spatial modeling & plot generator
├── reports/
│   └── Kanpur_LST_Analysis_Report.md         # Comprehensive formal scientific report
├── requirements.txt
├── LICENSE                                   # MIT License
└── README.md
```

---

## License & Attribution

- **Code & Geospatial Assets**: Open source under the [MIT License](LICENSE).
- **Satellite Data**: Courtesy of the NASA POWER Project (MERRA-2 Reanalysis), NASA Langley Research Center.
- **Author**: Avnish Singh (HBTU Kanpur &middot; Signal Earth).
