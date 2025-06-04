import argparse


def parse_limit(limit_str: str) -> tuple[float, float]:
    """Parse a limit string in the format 'min,max' into a tuple of floats."""
    try:
        lower, upper = map(float, limit_str.split(","))
        return lower, upper
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Limit must be two comma-separated numbers (got '{limit_str}')"
        )
