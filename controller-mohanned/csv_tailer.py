from __future__ import annotations

"""
CSV file tailer.

Watches a CSV file (produced by CICFlowMeter) for newly appended rows
and yields them as dictionaries (column_name -> value).

Uses a simple seek-based polling approach -- no external dependencies.
"""

import csv
import io
import os
import time

from config import FLOWS_CSV_PATH, TAIL_POLL_INTERVAL


class CSVTailer:
    """Tails a CSV file and yields new rows as dicts."""

    def __init__(
        self,
        path: str = FLOWS_CSV_PATH,
        poll_interval: float = TAIL_POLL_INTERVAL,
    ):
        self.path = path
        self.poll_interval = poll_interval
        self._headers: list[str] | None = None
        self._position: int = 0
        self._partial_line: str = ""

    # -- public API ------------------------------------------

    def follow(self):
        """
        Generator that yields new CSV rows as dicts, forever.

        Waits for the file to be created (CICFlowMeter may take a
        moment to start writing), then reads the header row, and
        continuously yields new data rows as they are appended.
        """
        self._wait_for_file()
        self._read_header()

        print(
            f"[TAILING] {self.path}  "
            f"({len(self._headers)} columns detected)",
            flush=True,
        )

        while True:
            rows = self._read_new_rows()
            for row in rows:
                yield row

            if not rows:
                time.sleep(self.poll_interval)

    # -- internals -------------------------------------------

    def _wait_for_file(self) -> None:
        """Block until the CSV file exists and has content."""
        print(
            f"[WAITING] Waiting for CICFlowMeter to create {self.path}...",
            flush=True,
        )
        while True:
            if os.path.exists(self.path) and os.path.getsize(self.path) > 0:
                return
            time.sleep(self.poll_interval)

    def _read_header(self) -> None:
        """Read and store the CSV header row."""
        with open(self.path, "r") as f:
            first_line = f.readline().strip()
            if not first_line:
                raise RuntimeError(
                    f"CSV file {self.path} exists but has no header row"
                )
            reader = csv.reader(io.StringIO(first_line))
            self._headers = next(reader)
            self._position = f.tell()

        print(f"[HEADERS] {self._headers}", flush=True)

    def _read_new_rows(self) -> list[dict]:
        """Read any new complete lines appended since last check."""
        rows: list[dict] = []

        try:
            with open(self.path, "r") as f:
                f.seek(self._position)
                raw = self._partial_line + f.read()
                self._position = f.tell()
        except FileNotFoundError:
            return rows

        if not raw:
            return rows

        # Split into lines; last element may be a partial line
        lines = raw.split("\n")
        if raw.endswith("\n"):
            self._partial_line = ""
        else:
            self._partial_line = lines.pop()

        for line in lines:
            line = line.strip()
            if not line:
                continue
            reader = csv.reader(io.StringIO(line))
            values = next(reader)
            if len(values) != len(self._headers):
                # Malformed row -- skip
                print(
                    f"[WARN] Skipping malformed row "
                    f"({len(values)} cols, expected {len(self._headers)})",
                    flush=True,
                )
                continue
            rows.append(dict(zip(self._headers, values)))

        return rows
