import dataclasses
from typing import Optional, Tuple

import numpy as np


@dataclasses.dataclass
class VPMParams:
    epsilon_max: float = 0.68
    tmin: float = 0.0
    tmax: float = 40.0
    topt: float = 25.0
    fpar_method: str = "evi_linear"  # evi_linear or evi_minmax
    fpar_a: float = 1.25
    fpar_b: float = 0.0
    evi_min: float = 0.05
    evi_max: float = 0.95
    npp_ratio: float = 0.5
    carbon_fraction: float = 0.45
    pscalar_mode: str = "constant"  # constant or lswi
    pscalar_constant: float = 1.0


def _safe_divide(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    return np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator != 0)


def fpar_from_evi(evi: np.ndarray, params: VPMParams) -> np.ndarray:
    if params.fpar_method == "evi_linear":
        fpar = params.fpar_a * evi + params.fpar_b
    elif params.fpar_method == "evi_minmax":
        fpar = _safe_divide(evi - params.evi_min, params.evi_max - params.evi_min)
    else:
        raise ValueError(f"Unsupported fpar_method: {params.fpar_method}")
    return np.clip(fpar, 0.0, 1.0)


def tscalar(tmean: np.ndarray, params: VPMParams) -> np.ndarray:
    tmin, tmax, topt = params.tmin, params.tmax, params.topt
    numerator = (tmean - tmin) * (tmean - tmax)
    denominator = (tmean - tmin) * (tmean - tmax) - (tmean - topt) ** 2
    scalar = _safe_divide(numerator, denominator)
    return np.clip(scalar, 0.0, 1.0)


def wscalar(lswi: np.ndarray, lswi_max: np.ndarray) -> np.ndarray:
    return _safe_divide(1.0 + lswi, 1.0 + lswi_max)


def pscalar(lswi: np.ndarray, lswi_max: np.ndarray, params: VPMParams) -> np.ndarray:
    if params.pscalar_mode == "lswi":
        return wscalar(lswi, lswi_max)
    if params.pscalar_mode == "constant":
        return np.full_like(lswi, params.pscalar_constant)
    raise ValueError(f"Unsupported pscalar_mode: {params.pscalar_mode}")


def compute_gpp(
    evi: np.ndarray,
    lswi: np.ndarray,
    par: np.ndarray,
    tmean: np.ndarray,
    params: Optional[VPMParams] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute GPP, NPP, and biomass for a time series.

    Inputs are arrays shaped (time, rows, cols).
    Returns cumulative sums for GPP/NPP/biomass with shape (rows, cols).
    """
    if params is None:
        params = VPMParams()

    if not (evi.shape == lswi.shape == par.shape == tmean.shape):
        raise ValueError("All input arrays must share the same shape (time, rows, cols)")

    lswi_max = np.nanmax(lswi, axis=0)

    fpar = fpar_from_evi(evi, params)
    tsca = tscalar(tmean, params)
    wsca = wscalar(lswi, lswi_max)
    psca = pscalar(lswi, lswi_max, params)

    epsilon_g = params.epsilon_max * tsca * wsca * psca
    gpp = par * fpar * epsilon_g

    gpp_sum = np.nansum(gpp, axis=0)
    npp_sum = gpp_sum * params.npp_ratio
    biomass_sum = npp_sum / params.carbon_fraction

    return gpp_sum, npp_sum, biomass_sum
