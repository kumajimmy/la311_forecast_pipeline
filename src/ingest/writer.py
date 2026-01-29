"""Write records to partitioned JSONL.gz files."""

import gzip
import json
import logging
import os
import tempfile
from datetime import date
from pathlib import Path

from . import config

log = logging.getLogger(__name__)


def partition_path(day: date) -> Path:
    """Return the canonical path for a day's raw file."""
    return (
        Path(config.RAW_DIR)
        / f"date={day.isoformat()}"
        / f"la311_{day.strftime('%Y%m%d')}.jsonl.gz"
    )


def write_day(day: date, records: list[dict]) -> Path:
    """Atomically write *records* as gzipped JSONL to the partition path."""
    dest = partition_path(day)
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists():
        log.warning("Overwriting existing partition: %s", dest)

    fd, tmp = tempfile.mkstemp(dir=dest.parent, suffix=".tmp")
    os.close(fd)
    try:
        with gzip.open(tmp, "wt", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, separators=(",", ":")) + "\n")
        os.replace(tmp, dest)
    except BaseException:
        os.unlink(tmp)
        raise

    log.info("Wrote %d records -> %s", len(records), dest)
    return dest
