


"""
file_handler.py

Handles uploaded CSV/Excel files, detects barcode and quantity columns
by value pattern recognition, validates barcodes against your DB,
and returns clean split results ready for downstream action.

DB functions (get_item_from_db, get_items_batch_from_db) live here
alongside the file handling logic and share the same DATABASE_URL.
"""

import pandas as pd
from dataclasses import dataclass, field
from typing import Optional
from pydantic import BaseModel, field_validator

from common.db.crud.items import get_items_batch_from_db
from backend.services.async_runner import run_async       # your run_async wrapper


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

@dataclass
class Pattern:
    regex: str
    confidence: float
    description: str
    examples: list[str]


BARCODE_PATTERNS = [
    Pattern(
        regex=r"^\d{13}$",
        confidence=0.99,
        description="EAN-13",
        examples=["5901234123457", "4006381333931", "0012345678905"],
    ),
    Pattern(
        regex=r"^\d{12}$",
        confidence=0.99,
        description="UPC-A",
        examples=["012345678905", "123456789012", "075678164125"],
    ),
    Pattern(
        regex=r"^\d{8}$",
        confidence=0.95,
        description="EAN-8",
        examples=["73513537", "40170725", "12345670"],
    ),
    Pattern(
        regex=r"^\d{8,14}$",
        confidence=0.90,
        description="generic numeric barcode",
        examples=["123456789", "12345678901", "1234567890123"],
    ),
]

QUANTITY_PATTERNS = [
    Pattern(
        regex=r"^\d+$",
        confidence=0.95,
        description="whole number",
        examples=["1", "42", "1000"],
    ),
    Pattern(
        regex=r"^\d+\.0+$",
        confidence=0.90,
        description="whole number as float (Excel export)",
        examples=["0.5", "1.0", "42.0", "1000.00"],
    ),
]


# ---------------------------------------------------------------------------
# Column detection
# ---------------------------------------------------------------------------

@dataclass
class DetectedColumns:
    barcode_col: Optional[str] = None
    quantity_col: Optional[str] = None
    barcode_confidence: float = 0.0
    quantity_confidence: float = 0.0
    extra_columns: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return self.barcode_col is not None and self.quantity_col is not None


class ColumnDetector:
    def __init__(self, sample_size: int = 50, min_match_ratio: float = 0.85):
        self.sample_size = sample_size
        self.min_match_ratio = min_match_ratio

    def detect(self, df: pd.DataFrame) -> DetectedColumns:
        scores: dict[str, dict[str, float]] = {}

        for col in df.columns:
            sample = self._sample(df[col])
            if sample is None:
                continue
            scores[col] = {
                "barcode": self._score(sample, BARCODE_PATTERNS),
                "quantity": self._score(sample, QUANTITY_PATTERNS),
            }

        barcode_col, barcode_conf = self._best(scores, "barcode")
        quantity_col, quantity_conf = self._best(scores, "quantity")

        # Edge case: same column won both — give quantity to next best
        if barcode_col and barcode_col == quantity_col:
            quantity_col, quantity_conf = self._best(scores, "quantity", exclude=barcode_col)

        mapped = {c for c in [barcode_col, quantity_col] if c}
        extra = [c for c in df.columns if c not in mapped]

        return DetectedColumns(
            barcode_col=barcode_col,
            quantity_col=quantity_col,
            barcode_confidence=barcode_conf,
            quantity_confidence=quantity_conf,
            extra_columns=extra,
        )

    def _sample(self, series: pd.Series) -> Optional[pd.Series]:
        s = series.dropna().astype(str).str.strip()
        s = s[s != ""].head(self.sample_size)
        return s if len(s) > 0 else None

    def _score(self, sample: pd.Series, patterns: list[Pattern]) -> float:
        for p in patterns:
            ratio = sample.str.match(p.regex).mean()
            if ratio >= self.min_match_ratio:
                return p.confidence * ratio
        return 0.0

    def _best(
        self, scores: dict, field: str, exclude: str = None
    ) -> tuple[Optional[str], float]:
        candidates = {
            col: s[field]
            for col, s in scores.items()
            if s[field] > 0 and col != exclude
        }
        if not candidates:
            return None, 0.0
        best_col = max(candidates, key=candidates.get)
        return best_col, candidates[best_col]


# ---------------------------------------------------------------------------
# Pydantic row model
# ---------------------------------------------------------------------------

class InventoryRow(BaseModel):
    barcode: str
    quantity: int

    @field_validator("barcode")
    @classmethod
    def clean_barcode(cls, v: str) -> str:
        v = str(v).strip()
        if not v:
            raise ValueError("Empty barcode")
        return v

    @field_validator("quantity", mode="before")
    @classmethod
    def parse_quantity(cls, v) -> int:
        try:
            return int(float(str(v).strip()))  # handles "5.0" from Excel
        except (ValueError, TypeError):
            raise ValueError(f"Cannot parse quantity: {v!r}")


# ---------------------------------------------------------------------------
# Parse result
# ---------------------------------------------------------------------------

@dataclass
class ParseResult:
    """
    valid_rows:   passed format validation + found in Supabase DB
    not_found:    passed format validation but barcode not in DB
    invalid_rows: failed Pydantic validation (bad format, unparseable quantity)
    """
    valid_rows: list[InventoryRow] = field(default_factory=list)
    not_found: list[dict] = field(default_factory=list)   # {"row": int, "barcode": str, "quantity": int}
    invalid_rows: list[dict] = field(default_factory=list) # {"row": int, "error": str}

    @property
    def has_valid(self) -> bool:
        return len(self.valid_rows) > 0

    @property
    def summary(self) -> str:
        parts = [f"{len(self.valid_rows)} valid"]
        if self.not_found:
            parts.append(f"{len(self.not_found)} not found in DB")
        if self.invalid_rows:
            parts.append(f"{len(self.invalid_rows)} invalid format")
        return " · ".join(parts)


# ---------------------------------------------------------------------------
# Main handler
# ---------------------------------------------------------------------------

class InventoryFileHandler:
    """
    Usage:
        handler = InventoryFileHandler(DATABASE_URL)
        detected, result = handler.process(uploaded_file)

        if not detected.is_valid:
            # could not identify barcode/quantity columns — show error
            ...

        # result.valid_rows   → known barcodes, trigger your action
        # result.not_found    → tell user these barcodes were not found
        # result.invalid_rows → tell user these rows had bad data
    """

    def __init__(self, database_url: str, batch_size: int = 500):
        self.database_url = database_url
        self.batch_size = batch_size
        self.detector = ColumnDetector()

    def process(
        self,
        uploaded_file,
        barcode_col_override: str = None,
        quantity_col_override: str = None,
    ) -> tuple[DetectedColumns, Optional[ParseResult]]:
        """
        Main entry point.
        Returns (DetectedColumns, ParseResult) or (DetectedColumns, None)
        if columns could not be identified.

        Pass overrides if the user manually corrected columns in the UI.
        """
        df = self._read(uploaded_file)
        detected = self.detector.detect(df)

        if barcode_col_override:
            detected.barcode_col = barcode_col_override
        if quantity_col_override:
            detected.quantity_col = quantity_col_override

        if not detected.is_valid:
            return detected, None

        result = self._parse_and_validate(df, detected)
        return detected, result

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _read(self, uploaded_file) -> pd.DataFrame:
        name = uploaded_file.name.lower()
        if name.endswith(".csv"):
            # dtype=str preserves leading zeros in barcodes
            return pd.read_csv(uploaded_file, dtype=str)
        elif name.endswith((".xlsx", ".xls")):
            return pd.read_excel(uploaded_file, dtype=str)
        raise ValueError(
            f"Unsupported file type: '{uploaded_file.name}'. Use CSV or Excel."
        )

    def _parse_and_validate(
        self, df: pd.DataFrame, detected: DetectedColumns
    ) -> ParseResult:
        """Step 1: Pydantic format validation. Step 2: single batch DB lookup."""
        format_valid: list[tuple[int, InventoryRow]] = []
        invalid_rows: list[dict] = []

        for i, row in df.iterrows():
            try:
                item = InventoryRow(
                    barcode=row[detected.barcode_col],
                    quantity=row[detected.quantity_col],
                )
                format_valid.append((i, item))
            except Exception as e:
                invalid_rows.append({
                    "row": i + 2,   # +2: 1-indexed + header row
                    "error": str(e),
                })

        # One DB round-trip for all format-valid barcodes
        barcodes = [item.barcode for _, item in format_valid]
        known = self._lookup_barcodes(barcodes)

        valid_rows: list[InventoryRow] = []
        not_found: list[dict] = []

        for _, item in format_valid:
            if item.barcode in known:
                valid_rows.append(item)
            else:
                not_found.append({
                    "barcode": item.barcode,
                    "quantity": item.quantity,
                })

        return ParseResult(
            valid_rows=valid_rows,
            not_found=not_found,
            invalid_rows=invalid_rows,
        )

    def _lookup_barcodes(self, barcodes: list[str]) -> set[str]:
        """
        Runs get_items_batch_from_db via run_async.
        Batches to avoid oversized IN clauses on very large files.
        """
        if not barcodes:
            return set()

        found: set[str] = set()

        for i in range(0, len(barcodes), self.batch_size):
            batch = barcodes[i:i + self.batch_size]
            result = run_async(
                get_items_batch_from_db, DATABASE_URL=self.database_url, item_codes=batch)
            found.update(result)

        return found