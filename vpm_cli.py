import argparse
from pathlib import Path

import numpy as np
import rasterio

from vpm import VPMParams, compute_gpp


def read_stack(path: Path) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as src:
        data = src.read().astype("float32")
        profile = src.profile
    return data, profile


def write_raster(path: Path, data: np.ndarray, profile: dict) -> None:
    out_profile = profile.copy()
    out_profile.update(count=1, dtype="float32")
    with rasterio.open(path, "w", **out_profile) as dst:
        dst.write(data.astype("float32"), 1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="VPM GPP/NPP/Biomass calculator (Xiao 2004).")
    parser.add_argument("--evi", required=True, type=Path, help="EVI GeoTIFF (time as bands)")
    parser.add_argument("--lswi", required=True, type=Path, help="LSWI GeoTIFF (time as bands)")
    parser.add_argument("--par", required=True, type=Path, help="PAR GeoTIFF (time as bands)")
    parser.add_argument("--tmean", required=True, type=Path, help="Tmean GeoTIFF (time as bands)")
    parser.add_argument("--out-gpp", required=True, type=Path, help="Output cumulative GPP GeoTIFF")
    parser.add_argument("--out-npp", required=True, type=Path, help="Output cumulative NPP GeoTIFF")
    parser.add_argument("--out-biomass", required=True, type=Path, help="Output cumulative biomass GeoTIFF")

    parser.add_argument("--epsilon-max", type=float, default=0.68)
    parser.add_argument("--tmin", type=float, default=0.0)
    parser.add_argument("--tmax", type=float, default=40.0)
    parser.add_argument("--topt", type=float, default=25.0)
    parser.add_argument("--fpar-method", choices=["evi_linear", "evi_minmax"], default="evi_linear")
    parser.add_argument("--fpar-a", type=float, default=1.25)
    parser.add_argument("--fpar-b", type=float, default=0.0)
    parser.add_argument("--evi-min", type=float, default=0.05)
    parser.add_argument("--evi-max", type=float, default=0.95)
    parser.add_argument("--npp-ratio", type=float, default=0.5)
    parser.add_argument("--carbon-fraction", type=float, default=0.45)
    parser.add_argument("--pscalar-mode", choices=["constant", "lswi"], default="constant")
    parser.add_argument("--pscalar-constant", type=float, default=1.0)

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    evi, profile = read_stack(args.evi)
    lswi, _ = read_stack(args.lswi)
    par, _ = read_stack(args.par)
    tmean, _ = read_stack(args.tmean)

    params = VPMParams(
        epsilon_max=args.epsilon_max,
        tmin=args.tmin,
        tmax=args.tmax,
        topt=args.topt,
        fpar_method=args.fpar_method,
        fpar_a=args.fpar_a,
        fpar_b=args.fpar_b,
        evi_min=args.evi_min,
        evi_max=args.evi_max,
        npp_ratio=args.npp_ratio,
        carbon_fraction=args.carbon_fraction,
        pscalar_mode=args.pscalar_mode,
        pscalar_constant=args.pscalar_constant,
    )

    gpp_sum, npp_sum, biomass_sum = compute_gpp(evi, lswi, par, tmean, params)

    write_raster(args.out_gpp, gpp_sum, profile)
    write_raster(args.out_npp, npp_sum, profile)
    write_raster(args.out_biomass, biomass_sum, profile)


if __name__ == "__main__":
    main()
