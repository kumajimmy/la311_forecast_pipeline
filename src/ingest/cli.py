"""CLI entrypoint for LA 311 ingestion."""

import argparse
import logging
import sys
from datetime import date, timedelta

from . import client, writer

log = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Ingest LA 311 data to raw partitions.")
    p.add_argument("--date", type=date.fromisoformat, help="Single date (YYYY-MM-DD)")
    p.add_argument("--start", type=date.fromisoformat, help="Range start (inclusive)")
    p.add_argument("--end", type=date.fromisoformat, help="Range end (inclusive)")
    p.add_argument("--limit", type=int, default=None, help="Max records per day (for testing)")
    return p.parse_args(argv)


def resolve_dates(args: argparse.Namespace) -> list[date]:
    if args.date:
        return [args.date]
    if args.start and args.end:
        days = []
        d = args.start
        while d <= args.end:
            days.append(d)
            d += timedelta(days=1)
        return days
    # default: yesterday
    return [date.today() - timedelta(days=1)]


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    args = parse_args(argv)
    dates = resolve_dates(args)
    log.info("Ingesting %d day(s): %s .. %s", len(dates), dates[0], dates[-1])

    for day in dates:
        records = client.fetch_day(day, limit=args.limit)
        if records:
            writer.write_day(day, records)
        else:
            log.warning("No records for %s", day)


if __name__ == "__main__":
    main()
