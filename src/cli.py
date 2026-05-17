import argparse
import logging
import sys
from pathlib import Path

from .config import load as load_config
from .runner import run
from .scheduler import run_once, run_loop


def main() -> None:
    args = _parse_args()
    _configure_logging(args.verbose, args.quiet)

    try:
        config = load_config(args.config)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error loading config: {exc}", file=sys.stderr)
        sys.exit(1)

    config = _apply_overrides(config, args)

    job = lambda: run(config, dry_run=args.dry_run)

    if args.once:
        run_once(job)
    else:
        interval = args.interval or config["scheduling"]["interval_seconds"]
        run_loop(job, interval_seconds=interval)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="gumtree-scraper",
        description="Monitor Gumtree listings and alert on new matches.",
    )

    parser.add_argument(
        "--config", "-c",
        type=Path,
        default=Path(__file__).parent.parent / "config" / "settings.yaml",
        metavar="PATH",
        help="Path to settings.yaml (default: config/settings.yaml)",
    )

    # Run mode
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--once",
        action="store_true",
        help="Run a single scrape and exit (default: poll continuously)",
    )
    mode.add_argument(
        "--interval", "-i",
        type=float,
        metavar="SECONDS",
        help="Polling interval in seconds (overrides config)",
    )

    # Filter overrides
    parser.add_argument("--min-price", type=int, metavar="N", help="Minimum price filter")
    parser.add_argument("--max-price", type=int, metavar="N", help="Maximum price filter")
    parser.add_argument("--location", metavar="TEXT", help="Location substring filter")
    parser.add_argument(
        "--seller-type",
        choices=["private", "dealer", "all"],
        metavar="TYPE",
        help="Seller type: private, dealer, or all",
    )

    # Output format overrides
    output = parser.add_argument_group("output format")
    output.add_argument("--csv", dest="csv", action="store_true", default=None, help="Enable CSV output")
    output.add_argument("--json", dest="json", action="store_true", default=None, help="Enable JSON output")
    output.add_argument("--sqlite", dest="sqlite", action="store_true", default=None, help="Enable SQLite output")

    # Modes
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print results to stdout; skip saving and notifications",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable DEBUG logging")
    parser.add_argument("--quiet", "-q", action="store_true", help="Only log warnings and errors")

    return parser.parse_args()


def _apply_overrides(config: dict, args: argparse.Namespace) -> dict:
    if args.min_price is not None:
        config["filters"]["price"]["min"] = args.min_price
    if args.max_price is not None:
        config["filters"]["price"]["max"] = args.max_price
    if args.location is not None:
        config["filters"]["location"] = args.location
    if args.seller_type is not None:
        config["filters"]["seller_type"] = args.seller_type

    output = config["features"]["output"]
    if args.csv:
        output["csv"] = True
    if args.json:
        output["json"] = True
    if args.sqlite:
        output["sqlite"] = True

    return config


def _configure_logging(verbose: bool, quiet: bool) -> None:
    if verbose:
        level = logging.DEBUG
    elif quiet:
        level = logging.WARNING
    else:
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger().setLevel(level)
