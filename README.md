# VPM-based GPP/NPP/Biomass workflow (Liaohe Estuary, 2025)

This repository provides a minimal, reproducible workflow to compute growing-season cumulative **GPP** using the **Vegetation Photosynthesis Model (VPM)** from **Xiao et al., 2004** and then convert **GPP → NPP → biomass**.

## Model overview (Xiao 2004)

VPM estimates GPP as:

```
GPP = PAR * FPAR * εg
εg = εmax * Tscalar * Wscalar * Pscalar
```

Where:
- **FPAR** is derived from Sentinel-2 EVI (or NDVI as a fallback).
- **Tscalar** is a temperature scalar driven by air temperature.
- **Wscalar** is a moisture scalar based on LSWI.
- **Pscalar** is a phenology scalar (often 1 for non-evergreen vegetation).

The script in this repo implements these equations and supports cumulative growing-season aggregation and conversion to NPP and biomass.

## Inputs

You need **co-registered** rasters for each time step (e.g., 8‑day or 10‑day):

- **EVI** (or NDVI)
- **LSWI**
- **PAR** (photosynthetically active radiation, MJ m⁻² per timestep)
- **Tmean** (°C; or derive from Tmin/Tmax externally)

Each input should be a GeoTIFF with one band per timestep in the same order.

> Sentinel‑2 can provide reflectance to derive EVI/LSWI. PAR and Tmean are typically from reanalysis or ground meteorology.

## Quick start

```bash
python vpm_cli.py \
  --evi data/evi_2025.tif \
  --lswi data/lswi_2025.tif \
  --par data/par_2025.tif \
  --tmean data/tmean_2025.tif \
  --out-gpp out/gpp_2025_sum.tif \
  --out-npp out/npp_2025_sum.tif \
  --out-biomass out/biomass_2025_sum.tif
```

## Key parameters

- `--epsilon-max` (εmax): default **0.68 gC MJ⁻¹**
- `--tmin`, `--tmax`, `--topt` (°C): temperature response parameters
- `--fpar-method`: `evi_linear` or `evi_minmax`
- `--npp-ratio`: default **0.5** (NPP/GPP)
- `--carbon-fraction`: default **0.45** (C fraction of dry biomass)

Adjust parameters for local vegetation types or literature values.

## Outputs

- **Cumulative GPP** for the 2025 growing season (gC m⁻²)
- **NPP** (gC m⁻²), converted from GPP by `npp_ratio`
- **Biomass** (g dry matter m⁻²), converted from NPP by `carbon_fraction`

## Notes on growing-season selection

Use only timesteps covering the 2025 growing season for Liaohe Estuary (e.g., April–October). If your input stacks include the whole year, pre-filter to the growing season before running the script.
