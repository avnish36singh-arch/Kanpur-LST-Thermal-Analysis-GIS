"""
Thermodynamic & Bioclimatic Analytical Engine: Kanpur LST & Urban Inversion Dynamics
Calculates boundary layer height proxy, ventilation coefficient, nocturnal inversion severity index (NISI),
NOAA bioclimatic heat index, and surface urban heat island intensity (SUHII).
"""

import numpy as np
import pandas as pd


def compute_heat_index_celsius(t2m_c: float, rh_pct: float) -> float:
    """
    Computes NOAA/NWS Heat Index (apparent temperature) in Celsius using Rothfusz regression equation.
    Valid for temperatures >= 20°C and RH >= 0%.
    """
    if pd.isna(t2m_c) or pd.isna(rh_pct):
        return np.nan
    if t2m_c < 20.0:
        return t2m_c  # Heat index is not defined below 20°C (68°F), returns dry-bulb air temp

    # Convert to Fahrenheit
    T = t2m_c * 9.0 / 5.0 + 32.0
    R = rh_pct

    # Simple formula first
    hi_simple = 0.5 * (T + 61.0 + ((T - 68.0) * 1.2) + (R * 0.094))
    if hi_simple < 80.0:
        hi_f = hi_simple
    else:
        # Full Rothfusz regression
        hi_f = (
            -42.379
            + 2.04901523 * T
            + 10.14333127 * R
            - 0.22475541 * T * R
            - 0.00683783 * T * T
            - 0.05481717 * R * R
            + 0.00122874 * T * T * R
            + 0.00085282 * T * R * R
            - 0.00000199 * T * T * R * R
        )
        # Adjustments for low RH / high RH
        if R < 13.0 and 80.0 <= T <= 112.0:
            adj = ((13.0 - R) / 4.0) * np.sqrt((17.0 - abs(T - 95.0)) / 17.0)
            hi_f -= adj
        elif R > 85.0 and 80.0 <= T <= 87.0:
            adj = ((R - 85.0) / 10.0) * ((87.0 - T) / 5.0)
            hi_f += adj

    # Convert back to Celsius
    return (hi_f - 32.0) * 5.0 / 9.0


def categorize_heat_index(hi_c: float) -> str:
    """Classifies Heat Index into standard NOAA bioclimatic risk bands."""
    if pd.isna(hi_c):
        return "Unknown"
    if hi_c < 27.0:
        return "Normal / Safe"
    elif hi_c < 32.0:
        return "Caution"
    elif hi_c < 41.0:
        return "Extreme Caution"
    elif hi_c < 54.0:
        return "Danger"
    else:
        return "Extreme Danger"


def estimate_boundary_layer_height(delta_t: float, solar_radiation: float, wind_speed: float) -> float:
    """
    Estimates daily effective Planetary Boundary Layer Height (PBLH in meters) proxy.
    Under radiational cooling (Delta T < 0), the boundary layer collapses down to 150-350m.
    Under daytime solar insolation (Delta T > 0), convective mixing lifts the PBLH to 1200-2400m.
    """
    if pd.isna(delta_t) or pd.isna(wind_speed):
        return np.nan

    sw = solar_radiation if pd.notna(solar_radiation) and solar_radiation > 0 else 100.0
    ws = max(0.5, wind_speed)

    if delta_t < 0:
        # Radiative cooling inversion: shallow nocturnal/winter boundary layer
        pblh = 160.0 + 340.0 * np.exp(0.9 * delta_t) + 40.0 * ws
        return float(np.clip(pblh, 150.0, 650.0))
    else:
        # Convective thermal mixing: deep pre-monsoon/summer boundary layer
        pblh = 550.0 + 4.8 * sw + 140.0 * np.sqrt(delta_t) + 60.0 * ws
        return float(np.clip(pblh, 650.0, 2600.0))


def compute_ventilation_coefficient(pblh_m: float, wind_speed_mps: float) -> float:
    """
    Computes the Atmospheric Ventilation Coefficient:
    Vc = PBLH (m) * Wind Speed (m/s)  [Units: m²/s]
    Values below 2,000 m²/s indicate severe air stagnation where pollutants are entrapped.
    """
    if pd.isna(pblh_m) or pd.isna(wind_speed_mps):
        return np.nan
    return round(float(pblh_m * max(0.2, wind_speed_mps)), 1)


def categorize_ventilation(vc: float) -> str:
    """Classifies ventilation coefficient into carrying capacity tiers."""
    if pd.isna(vc):
        return "Unknown"
    if vc < 2000.0:
        return "Severe Stagnation"
    elif vc < 4000.0:
        return "Poor Dispersion"
    elif vc < 6000.0:
        return "Moderate Dispersion"
    else:
        return "Good Dispersion"


def compute_nocturnal_inversion_severity_index(delta_t: float, rh_pct: float, wind_speed: float) -> float:
    """
    Nocturnal Inversion Severity Index (NISI):
    Quantifies the atmospheric stability trapping potency.
    NISI = max(0, -Delta_T) * (1 + RH / 100) / max(1.0, WS)
    
    - 0.0: No inversion (Neutral or Convective)
    - 0.0 - 0.8: Weak Inversion
    - 0.8 - 1.8: Moderate Inversion
    - > 1.8: Severe Inversion Trap
    """
    if pd.isna(delta_t):
        return np.nan
    if delta_t >= 0:
        return 0.0

    rh = rh_pct if pd.notna(rh_pct) else 50.0
    ws = wind_speed if pd.notna(wind_speed) else 2.0

    cooling_mag = abs(delta_t)
    rh_factor = 1.0 + (rh / 100.0)
    wind_damping = max(1.0, ws)

    nisi = (cooling_mag * rh_factor) / wind_damping
    return round(float(nisi), 2)


def categorize_nisi(nisi: float) -> str:
    """Classifies NISI into operational meteorological alert tiers."""
    if pd.isna(nisi):
        return "Unknown"
    if nisi == 0.0:
        return "Convective / Mixing"
    elif nisi <= 0.8:
        return "Weak Inversion"
    elif nisi <= 1.8:
        return "Moderate Inversion"
    else:
        return "Severe Inversion Trap"


def enrich_thermal_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enriches raw NASA POWER daily telemetry dataframe with all physical,
    bioclimatic, and boundary-layer inversion metrics.
    """
    enriched = df.copy()

    # Ensure Delta T and DTR exist
    if "Delta_T_Skin_Air_C" not in enriched.columns:
        enriched["Delta_T_Skin_Air_C"] = enriched["LST_Skin_C"] - enriched["Air_Temp_2M_C"]
    if "Diurnal_Thermal_Range_C" not in enriched.columns:
        enriched["Diurnal_Thermal_Range_C"] = enriched["Temp_Max_2M_C"] - enriched["Temp_Min_2M_C"]

    # Bioclimatic Heat Index
    enriched["Heat_Index_C"] = [
        compute_heat_index_celsius(t, r)
        for t, r in zip(enriched["Air_Temp_2M_C"], enriched["Relative_Humidity_Pct"])
    ]
    enriched["Heat_Risk_Category"] = enriched["Heat_Index_C"].apply(categorize_heat_index)

    # Planetary Boundary Layer Height (PBLH) Proxy
    enriched["PBLH_m"] = [
        estimate_boundary_layer_height(dt, sw, ws)
        for dt, sw, ws in zip(
            enriched["Delta_T_Skin_Air_C"],
            enriched["Solar_Radiation_MJ_m2"],
            enriched["Wind_Speed_2M_mps"],
        )
    ]

    # Ventilation Coefficient
    enriched["Ventilation_Coeff_m2s"] = [
        compute_ventilation_coefficient(p, ws)
        for p, ws in zip(enriched["PBLH_m"], enriched["Wind_Speed_2M_mps"])
    ]
    enriched["Ventilation_Category"] = enriched["Ventilation_Coeff_m2s"].apply(categorize_ventilation)

    # Nocturnal Inversion Severity Index (NISI)
    enriched["NISI"] = [
        compute_nocturnal_inversion_severity_index(dt, r, ws)
        for dt, r, ws in zip(
            enriched["Delta_T_Skin_Air_C"],
            enriched["Relative_Humidity_Pct"],
            enriched["Wind_Speed_2M_mps"],
        )
    ]
    enriched["Inversion_Category"] = enriched["NISI"].apply(categorize_nisi)

    return enriched
