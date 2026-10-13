"""Plot the error between OptiTrack and the gantry over time for the RoboLoc-G dataset.

For each take, the OptiTrack positions of the rigid body of the gantry ("Grua")
are aligned with the gantry positions. Then the error (aligned OptiTrack
position minus gantry position) is plotted against time.

The plots show:

The samples with an error of --dropout-mm or more are plotted in red. These are
the ones that ``validate_dataset.py`` excludes as tracking errors.
"""

import argparse
import logging
from pathlib import Path
from typing import Literal

import numpy as np
import numpy.typing as npt
import validate_dataset as vd
from data import CorrectionModel, load_correction
from defaults import CALIBRATION_FILE, DATASET_DIR

logger = logging.getLogger("plot_dataset_errors")

AXES_NAMES = ["X", "Y", "Z", "Abs"]

DEFAULT_OUTDIR = Path(__file__).resolve().parent / "dataset_error_plots"

FloatArray = npt.NDArray[np.float64]
BoolArray = npt.NDArray[np.bool_]


def compute_errors(
    take: str, model: CorrectionModel, target: vd.Target
) -> tuple[FloatArray, FloatArray, BoolArray]:
    """Compute the error between OptiTrack and the gantry in a take.

    ``target`` says which gantry positions are used: the ones corrected with
    ``model`` or the uncorrected ones.

    Returns:

    - The time of each sample, in seconds from the first one.
    - The error of each sample, in mm, with columns X, Y, Z and 3D distance.
      It is NaN in the samples that are not valid.
    - Bool array indicating the samples with an error of DROPOUT_MM or more.
    """
    optitrack, gantry_before, gantry_after, valid = vd.load_take(take, model)
    gantry = gantry_after if target == "corrected" else gantry_before

    # The alignment is fitted without the tracking errors of OptiTrack
    alignment = vd.fit_alignment_without_tracking_errors(optitrack, gantry, valid)

    error_xyz = vd.residual_vec(optitrack, gantry, alignment)
    error_abs = vd.residual_3d(optitrack, gantry, alignment)
    errors = np.column_stack([error_xyz, error_abs])

    time = optitrack["time"].to_numpy()
    time = time - time[0]

    excluded = valid & (error_abs >= vd.DROPOUT_MM) & ~np.isnan(error_abs)

    # With NaN, the samples that are not valid are shown as gaps in the plot
    errors[~valid] = np.nan

    logger.info(
        "[%s] target=%s  valid=%d  excluded(>%.0fmm)=%d",
        take,
        target,
        int(valid.sum()),
        vd.DROPOUT_MM,
        int(excluded.sum()),
    )
    return time, errors, excluded


def plot_take(
    take: str,
    time: FloatArray,
    errors: FloatArray,
    excluded: BoolArray,
    target: vd.Target,
    x_axis: Literal["seconds", "samples"],
    outdir: Path | None,
) -> None:
    """Plot the errors of a take, as returned by ``compute_errors``.

    The figure is saved in ``outdir``, or shown in a window if it is None.
    """
    import matplotlib.pyplot as plt

    dropout_mm = vd.DROPOUT_MM

    # Values of the horizontal axis
    if x_axis == "samples":
        x = np.arange(len(time), dtype=float)
        xlabel = "sample index"
    else:
        x = time
        xlabel = "time (s)"

    num_excluded = int(excluded.sum())

    fig, axs = plt.subplots(4, 1, figsize=(11, 8), sharex=True)
    fig.suptitle(
        f"{take}  (OptiTrack − {target} gantry, "
        f"{num_excluded} samples > {dropout_mm:g} mm)"
    )

    for i, (name, ax) in enumerate(zip(AXES_NAMES, axs)):
        # The labels of the legend are only set in the first plot
        first = i == 0

        ax.axhline(0.0, color="0.7", lw=0.8)

        ax.plot(x, errors[:, i], lw=0.6, color="tab:blue")

        # Mark in red the samples with an error over the threshold
        if num_excluded:
            ax.plot(
                x[excluded],
                errors[excluded, i],
                "o",
                ms=3,
                color="tab:red",
                label="excluded" if first else None,
            )

        if name == "Abs":
            # Line at the threshold
            ax.axhline(
                dropout_mm,
                color="tab:red",
                ls="--",
                lw=0.9,
                label=f"threshold {dropout_mm:g} mm",
            )
            ax.set_ylim(bottom=0)
            ax.set_ylabel("|e| (mm)")
        else:
            ax.set_ylabel(f"e_{name} (mm)")

        ax.grid(True, alpha=0.3)
        if first and num_excluded:
            ax.legend(loc="upper right", fontsize=8)

    axs[-1].set_xlabel(xlabel)
    fig.tight_layout(rect=(0, 0, 1, 0.98))

    if outdir is not None:
        outdir.mkdir(parents=True, exist_ok=True)
        filename = outdir / f"{take}_optitrack_error.png"
        fig.savefig(filename, dpi=120)
        logger.info("[%s] saved %s", take, filename)
    else:
        plt.show()
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--dataset-dir",
        type=Path,
        default=DATASET_DIR,
        help="dataset directory (must contain GROUND_TRUTH "
        "and OPTITRACK_MEASUREMENTS_CSV) (default: %(default)s)",
    )
    p.add_argument(
        "--calib",
        type=Path,
        default=CALIBRATION_FILE,
        help="calibration file with the parameters of the correction model "
        "(default: %(default)s)",
    )
    p.add_argument(
        "--takes",
        nargs="+",
        default=vd.TAKES,
        help="takes to plot (default: the 7 dynamic ones)",
    )
    p.add_argument(
        "--target",
        choices=["corrected", "uncorrected"],
        default="corrected",
        help="gantry positions used to compute the error. With 'corrected' the "
        "error is small and flat, so the tracking errors of OptiTrack are easy to "
        "see. With 'uncorrected' the error also includes the positioning error of "
        "the gantry, so it is larger and it changes along the take "
        "(default: %(default)s)",
    )
    p.add_argument(
        "--dropout-mm",
        type=float,
        default=vd.DROPOUT_MM,
        help="threshold of the 3D error (mm). The samples at this distance or more "
        "are marked in red (default: %(default)s)",
    )
    p.add_argument(
        "--x-axis",
        choices=["seconds", "samples"],
        default="seconds",
        help="horizontal axis of the plots: time in seconds or sample number "
        "(default: %(default)s)",
    )
    p.add_argument(
        "--save",
        action="store_true",
        help="save the plots as PNG files instead of showing them",
    )
    p.add_argument(
        "--outdir",
        type=Path,
        default=DEFAULT_OUTDIR,
        help="directory of the PNG files, used with --save (default: %(default)s)",
    )
    p.add_argument(
        "-q", "--quiet", action="store_true", help="do not print progress messages"
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(asctime)s  %(message)s",
        datefmt="%H:%M:%S",
    )

    # Matplotlib Agg backend does not need a window.
    # It has to be selected before importing pyplot.
    if args.save:
        import matplotlib

        matplotlib.use("Agg")

    # Override validate_dataset.py settings
    vd.DATASET_DIR = args.dataset_dir
    vd.GROUND_TRUTH_DIR = args.dataset_dir / "GROUND_TRUTH"
    vd.OPTITRACK_DIR = args.dataset_dir / "OPTITRACK_MEASUREMENTS_CSV"
    vd.DROPOUT_MM = args.dropout_mm

    model = load_correction(args.calib)
    outdir = args.outdir if args.save else None

    for take in args.takes:
        time, errors, excluded = compute_errors(take, model, args.target)
        plot_take(take, time, errors, excluded, args.target, args.x_axis, outdir)


if __name__ == "__main__":
    main()
