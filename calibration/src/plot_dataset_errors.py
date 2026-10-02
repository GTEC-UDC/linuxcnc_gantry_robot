"""
Plot the OptiTrack-vs-gantry positioning error (X, Y, Z and absolute) over time
for each RoboLoc-G take, to visually inspect for bad/glitch OptiTrack samples.

For each take the OptiTrack "Grua" rigid body is aligned to the gantry frame
(per-take rigid alignment, fitted with glitch rejection so the baseline is
clean), and the signed residual per axis plus the absolute 3D error are plotted
against time. Samples whose absolute error exceeds --dropout-mm (the glitch
threshold used by validate_dataset.py) are highlighted in red.

Reuses the loading/alignment machinery of validate_dataset.py.

Run (from this directory, using the local venv):
    .venv/bin/python plot_dataset_errors.py                # show interactively
    .venv/bin/python plot_dataset_errors.py --save         # save one PNG per take
    .venv/bin/python plot_dataset_errors.py --help
"""
import argparse
import json
import logging
from pathlib import Path

import numpy as np
import validate_dataset as vd
from defaults import CALIBRATION_FILE, DATASET_DIR

logger = logging.getLogger("plot_dataset_errors")

AXES = ["X", "Y", "Z", "Abs"]
DEFAULT_OUTDIR = Path(__file__).resolve().parent / "dataset_error_plots"


def compute_errors(take, corr_params, target="uncorrected"):
    """Return (t, err[N,4], valid, excluded) for a take.

    err columns are the signed residual X, Y, Z and the absolute 3D error, in
    the gantry frame after a glitch-clean per-take alignment.
    """
    df_rb, tgt_before, tgt_after, valid = vd.load_take(take, corr_params)
    tgt = tgt_after if target == "corrected" else tgt_before

    # alignment is fitted on the retained window (glitches + initial skip out),
    # but the residual is plotted over the full valid range so the excluded
    # transient stays visible.
    valid_fit = vd.apply_skip_initial(valid, df_rb)
    p = vd.fit_alignment(df_rb, tgt, mask=valid_fit)
    r = vd.residual_3d(df_rb, tgt, p)
    clean = valid_fit & (r < vd.DROPOUT_MM) & ~np.isnan(r)
    p = vd.fit_alignment(df_rb, tgt, mask=clean)

    rvec = vd.residual_vec(df_rb, tgt, p)          # (N, 3) signed, gantry frame
    rabs = vd.residual_3d(df_rb, tgt, p)           # (N,) absolute
    err = np.column_stack([rvec, rabs])            # (N, 4): X, Y, Z, Abs

    t = df_rb["time"].to_numpy()
    t = t - t[0]

    excluded = valid & (rabs >= vd.DROPOUT_MM) & ~np.isnan(rabs)
    # invalid rows -> NaN so they show as gaps, not spurious lines
    err[~valid] = np.nan
    logger.info("[%s] target=%s  valid=%d  excluded(>%.0fmm)=%d  skip=%.0fs",
                take, target, int(valid.sum()), vd.DROPOUT_MM,
                int(excluded.sum()), vd.SKIP_INITIAL_S)
    return t, err, valid, excluded


def plot_take(take, x, err, excluded, dropout_mm, target, skip_s, skip_end,
              xlabel, outdir, save):
    import matplotlib.pyplot as plt

    fig, axs = plt.subplots(4, 1, figsize=(11, 8), sharex=True)
    n_excl = int(excluded.sum())
    title = (f"{take}  (OptiTrack − {target} gantry, "
             f"{n_excl} samples > {dropout_mm:g} mm")
    title += f", skip first {skip_s:g} s)" if skip_s > 0 else ")"
    fig.suptitle(title)

    for i, ax in enumerate(AXES):
        a = axs[i]
        a.axhline(0.0, color="0.7", lw=0.8)
        if skip_end is not None:
            a.axvspan(x[0], skip_end, color="0.85", zorder=0,
                      label="skipped" if i == 0 else None)
        a.plot(x, err[:, i], lw=0.6, color="tab:blue")
        # highlight excluded (glitch) samples
        if n_excl:
            a.plot(x[excluded], err[excluded, i], "o", ms=3,
                   color="tab:red", label="excluded" if i == 0 else None)
        if ax == "Abs":
            a.axhline(dropout_mm, color="tab:red", ls="--", lw=0.9,
                      label=f"threshold {dropout_mm:g} mm")
            a.set_ylim(bottom=0)
        a.set_ylabel(f"e_{ax} (mm)" if ax != "Abs" else "|e| (mm)")
        a.grid(True, alpha=0.3)
        if i == 0 and (n_excl or skip_end is not None):
            a.legend(loc="upper right", fontsize=8)
    axs[-1].set_xlabel(xlabel)
    fig.tight_layout(rect=(0, 0, 1, 0.98))

    if save:
        outdir.mkdir(parents=True, exist_ok=True)
        out = outdir / f"{take}_optitrack_error.png"
        fig.savefig(out, dpi=120)
        logger.info("[%s] saved %s", take, out)
        plt.close(fig)
    else:
        plt.show()
        plt.close(fig)


def parse_args():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--dataset-dir", type=Path, default=DATASET_DIR,
                   help="dataset directory (GANTRY_MEASUREMENTS + "
                        "OPTITRACK_MEASUREMENTS_CSV)")
    p.add_argument("--calib", type=Path, default=CALIBRATION_FILE,
                   help="JSON file with the fixed correction parameters")
    p.add_argument("--takes", nargs="+", default=vd.TAKES,
                   help="takes to plot")
    p.add_argument("--target", choices=["corrected", "uncorrected"],
                   default="corrected",
                   help="gantry reference the error is computed against; "
                        "'corrected' gives a flat ~2 mm baseline where OptiTrack "
                        "glitches stand out, 'uncorrected' keeps the systematic "
                        "gantry structure (larger, wavy baseline)")
    p.add_argument("--dropout-mm", type=float, default=vd.DROPOUT_MM,
                   help="glitch threshold (mm): line + red highlight")
    p.add_argument("--skip-initial-s", type=float, default=vd.SKIP_INITIAL_S,
                   help="shade + exclude from the alignment fit the first N "
                        "seconds of each take (the approach transient)")
    p.add_argument("--x-axis", choices=["seconds", "samples"], default="seconds",
                   help="units of the X axis: elapsed time or sample index "
                        "(sample index matches the row numbers used elsewhere)")
    p.add_argument("--save", action="store_true",
                   help="save PNGs instead of showing figures interactively")
    p.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR,
                   help="directory for the PNG files (with --save)")
    p.add_argument("-q", "--quiet", action="store_true",
                   help="suppress progress logging")
    return p.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(asctime)s  %(message)s", datefmt="%H:%M:%S",
    )
    if args.save:
        import matplotlib
        matplotlib.use("Agg")

    # let overrides reach validate_dataset's module globals
    vd.DATASET_DIR = args.dataset_dir
    vd.GROUND_TRUTH_DIR = args.dataset_dir / "GROUND_TRUTH"
    vd.OPTITRACK_DIR = args.dataset_dir / "OPTITRACK_MEASUREMENTS_CSV"
    vd.DROPOUT_MM = args.dropout_mm
    vd.SKIP_INITIAL_S = args.skip_initial_s

    with open(args.calib) as f:
        corr_params = np.array(json.load(f)["correction"])

    for take in args.takes:
        t, err, _, excluded = compute_errors(take, corr_params, args.target)

        if args.x_axis == "samples":
            x = np.arange(len(t), dtype=float)
            xlabel = "sample index"
            # the skip window ends at the first sample past skip_initial_s
            skip_end = float(np.searchsorted(t, args.skip_initial_s))
        else:
            x = t
            xlabel = "time (s)"
            skip_end = args.skip_initial_s
        if args.skip_initial_s <= 0:
            skip_end = None

        plot_take(take, x, err, excluded, args.dropout_mm, args.target,
                  args.skip_initial_s, skip_end, xlabel, args.outdir, args.save)


if __name__ == "__main__":
    main()
