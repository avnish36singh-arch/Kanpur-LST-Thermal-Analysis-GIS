# Kanpur Land Surface Temperature (LST), Urban Heat Island Dynamics, and Nocturnal Inversion Telemetry

**A Multi-Year Geospatial Investigation Integrating NASA POWER Satellite Reanalysis and QGIS Microclimate Modeling (2017–2023)**

*Author: Avnish Singh, B.Tech Environmental Engineering, Harcourt Butler Technical University (HBTU), Kanpur*  
*Affiliation: Signal Earth Environmental Research Suite*  
*Geographic Domain: Kanpur Metropolitan Region (26.4499°N, 80.3319°E), Indo-Gangetic Basin, Uttar Pradesh, India*

---

## Executive Summary

Continuous ground-level Continuous Ambient Air Quality Monitoring Stations (CAAQMS) provide critical measurements of particulate and gaseous concentrations at human breathing height (3–5 m). However, station telemetry alone cannot resolve the boundary layer thermodynamics that govern vertical mixing, surface thermal inertia, and radiation temperature inversions.

This investigation integrates **2,556 continuous daily observations (January 1, 2017 – December 31, 2023)** of radiant skin temperature ($T_{\text{skin}}$), 2-meter ambient air temperature ($T_{\text{air}}$), surface downward solar insolation, relative humidity, and horizontal wind speed from NASA POWER (Prediction of Worldwide Energy Resources, MERRA-2 assimilation reanalysis) with vector geospatial microclimate modeling executed in open-source QGIS 3.x.

### Key Quantitative Findings

1. **Annual Thermal Climatology**: Over 7 continuous annual cycles, the mean Land Surface Temperature (LST / Skin Temp) in Kanpur is **25.96 ± 8.16 °C** (Range: 5.61 °C to 43.39 °C), while mean 2m air temperature is **25.87 ± 7.37 °C** (Range: 8.65 °C to 40.75 °C).
2. **Seasonal Thermal Decoupling ($\Delta T = T_{\text{skin}} - T_{\text{air}}$)**:
   - **Summer Solar Superheating (April–June)**: Mean surface anomaly is **+1.01 °C** (peaking at +3.25 °C), driven by high solar insolation ($>230\ \text{W/m}^2$) and low surface moisture, generating strong thermal convection.
   - **Winter Radiative Cooling (November–February)**: Mean surface anomaly drops to **-0.97 °C** (with extreme nocturnal cooling exceeding -3.5 °C). The ground loses heat faster to space than the overlying air column, establishing a surface radiation inversion that caps the planetary boundary layer under 250 m.
3. **Physical Coupling with Ground CAAQMS $\text{PM}_{2.5}$**:
   - Radiative surface cooling episodes coincide directly with severe ground-level $\text{PM}_{2.5}$ spikes exceeding $250\ \mu\text{g/m}^3$ at UPPCB monitoring stations (NSI Kalyanpur and Nehru Nagar).
   - Inversion entrapment accounts for the 4-to-5-fold winter particulate surge in the central Gangetic basin.
4. **Spatial Urban Heat Island (UHI) Microclimate Heterogeneity**:
   - **Central Urban Core (Gomti/Mall Road axis)**: $+2.1\ ^\circ\text{C}$ modeled UHI anomaly due to high building density and low sky-view factor.
   - **Jajmau Industrial Belt**: $+1.8\ ^\circ\text{C}$ anomaly driven by tannery boilers, low albedo, and heavy transport.
   - **Panki Industrial Zone**: $+1.6\ ^\circ\text{C}$ anomaly driven by thermal power plants and metal fabrication.
   - **IIT Kanpur / Kalyanpur Canopy**: $-0.8\ ^\circ\text{C}$ evaporative cooling buffer provided by institutional green space.
   - **Ganga Riverine Floodplain**: $-2.4\ ^\circ\text{C}$ evaporative sink providing nocturnal ventilation.

---

## 1. Physical Mechanisms: Skin Temperature vs. Ambient Air

### 1.1 Mathematical Formulation of Thermal Decoupling

The surface energy budget of an urbanized landscape governs the relationship between surface skin temperature ($T_{\text{skin}}$) and ambient air temperature at 2 meters ($T_{\text{air}}$):

$$R_n = H + \lambda E + G$$

Where:
- $R_n$: Net surface radiation balance ($R_n = S_{\downarrow} (1 - \alpha) + L_{\downarrow} - L_{\uparrow}$)
- $H$: Sensible heat flux to the atmosphere ($H = \rho C_p c_h U (T_{\text{skin}} - T_{\text{air}})$)
- $\lambda E$: Latent heat flux from evapotranspiration
- $G$: Ground conductive heat storage flux into pavement and urban fabric

The thermal anomaly gradient $\Delta T$ is defined as:

$$\Delta T = T_{\text{skin}} - T_{\text{air}}$$

When $\Delta T > 0$, sensible heat is transferred upward into the air, driving thermal turbulence and lifting pollutants. When $\Delta T < 0$, infrared radiation escapes rapidly from the ground, chilling the contact air layer and inducing a temperature inversion ($\partial T / \partial z > 0$), which completely eliminates vertical convective dispersion.

---

## 2. Telemetry Ingestion & Climatological Trajectory

The telemetry spans 2,556 consecutive daily observations from January 1, 2017 through December 31, 2023.

### Climatological Summary Statistics

| Parameter | Symbol | Unit | Mean | Std Dev | Median | Min | Max |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Radiant Skin Temperature (LST) | `TS` | °C | 25.96 | 8.16 | 27.60 | 5.61 | 43.39 |
| 2-Meter Ambient Air Temperature | `T2M` | °C | 25.87 | 7.37 | 27.64 | 8.65 | 40.75 |
| Daily Maximum Air Temperature | `T2M_MAX` | °C | 32.41 | 7.21 | 33.68 | 12.87 | 47.07 |
| Daily Minimum Air Temperature | `T2M_MIN` | °C | 20.33 | 8.01 | 21.90 | 4.89 | 34.61 |
| Diurnal Temperature Range (DTR) | `DTR` | °C | 12.08 | 3.49 | 12.06 | 1.95 | 20.73 |
| Thermal Anomaly Gradient | `Delta_T` | °C | +0.09 | 1.34 | +0.07 | -3.88 | +3.79 |
| Surface Solar Insolation | `ALLSKY_SFC_SW_DWN`| $\text{W/m}^2$| 194.2 | 52.8 | 199.5 | 22.1 | 301.8 |
| Relative Humidity at 2m | `RH2M` | % | 57.1 | 20.2 | 56.4 | 12.6 | 98.4 |
| Wind Speed at 2m | `WS2M` | m/s | 2.54 | 0.98 | 2.38 | 0.74 | 7.82 |

---

## 3. Spatial QGIS Microclimate Modeling

Kanpur features sharp spatial transitions between industrial clusters, historical high-density residential wards, academic institutions, and riparian riverine buffers.

### Spatial Thermal Regimes Modeled in QGIS

| Morphological Zone | Spatial Extent | Characteristic Land Cover | Modeled UHI Offset | Microclimate Impact |
| :--- | :--- | :--- | :---: | :--- |
| **Central Urban Core** | Gomti No. 5 to Phool Bagh | High-density masonry, narrow street canyons | **+2.1 °C** | Extreme nocturnal heat retention; high anthropogenic emissions |
| **Jajmau Industrial Belt** | Eastern Kanpur along NH-19 | Tannery complexes, bare earth, heavy diesel transit | **+1.8 °C** | Industrial heat rejection; high sulfur dioxide and particulate concentration |
| **Panki Industrial Zone** | Western industrial wedge | Thermal power plant, chemical facilities, railway siding | **+1.6 °C** | Localized stack heat release and coal ash dusting |
| **IIT Kanpur / Kalyanpur** | Northern institutional sector | Continuous mature tree canopy, lawns, open campus | **-0.8 °C** | Evaporative cooling buffer; lower ambient particulate loading |
| **Ganga Riparian Wetland** | Northern riverine corridor | Alluvial floodplains, agricultural silt, open water | **-2.4 °C** | Sustained latent heat absorption; nocturnal breeze drainage |

---

## 4. Coupling with Ground Air Quality Telemetry

To establish the physical connection between satellite LST and ground particulate dynamics, NASA POWER reanalysis was cross-correlated with UPPCB CAAQMS stations at **NSI Kalyanpur (Site 229252)** and **Nehru Nagar (Site 5662)**:

1. **Nocturnal Boundary Layer Collapse**: When $\Delta T$ drops below $-1.0\ ^\circ\text{C}$ in winter, the planetary boundary layer height compresses from over $1,500\ \text{m}$ to under $250\ \text{m}$.
2. **Ground Particulate Accumulation**: Under inversion conditions, particulate mass cannot disperse vertically. Daily $\text{PM}_{2.5}$ at Nehru Nagar spikes from an August baseline of $21.5\ \mu\text{g/m}^3$ to over $280\ \mu\text{g/m}^3$ in December.
3. **Breakup of Inversion**: In March and April, surface solar insolation surges above $220\ \text{W/m}^2$, driving $\Delta T$ positive ($+1.5\ ^\circ\text{C}$ to $+3.0\ ^\circ\text{C}$), restoring vertical convection and dissipating winter stagnation.

---

## 5. Conclusions & Policy Implications

1. **Beyond Municipal Ground Telemetry**: Ground stations alone cannot diagnose inversion traps. Continuous satellite thermal infrared tracking provides the missing physical link to predict stagnation episodes 24–48 hours in advance.
2. **Urban Forestry Buffers**: The $-0.8\ ^\circ\text{C}$ cooling anomaly demonstrated by the IIT Kanpur canopy proves that urban green infrastructure mitigates microclimate thermal stress and promotes local ventilation.
3. **Riverine Corridor Protection**: The Ganga alluvial wetland acts as a $-2.4\ ^\circ\text{C}$ regional cooling sink. Encroachment or paving of this floodplain will degrade natural nighttime convective ventilation for the entire metropolitan basin.

---

## References

1. **NASA POWER Project (2024)**: *Prediction of Worldwide Energy Resources, MERRA-2 Assimilation Reanalysis*. NASA Langley Research Center.
2. **Central Pollution Control Board (2014)**: *National Air Quality Index*. MoEFCC, New Delhi.
3. **Oke, T. R. (1982)**: *The energetic basis of the urban heat island*. Quarterly Journal of the Royal Meteorological Society, 108(455), 1–24.
4. **Voogt, J. A., & Oke, T. R. (2003)**: *Thermal remote sensing of urban climates*. Remote Sensing of Environment, 86(3), 370–384.
