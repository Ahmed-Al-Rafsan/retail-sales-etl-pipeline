"""Local batch pipeline with explicit validation and auditable outputs."""
import argparse
import hashlib
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

COLUMNS = ['OrderID', 'OrderDate', 'CustomerID', 'ProductID', 'ProductCategory',
           'ProductName', 'Quantity', 'UnitPrice', 'DiscountPct', 'ShippingState',
           'PaymentMethod', 'SalesChannel']


def transform(raw):
    """Return accepted, rejected, duplicate rows and reconciled counts.

    Gate: finite whole-number quantity and finite numeric price. Signs and
    business ranges are deliberately not constrained by this baseline contract.
    """
    if list(raw.columns) != COLUMNS:
        raise ValueError('Input columns must match the documented schema and order')
    duplicate_mask = raw.duplicated(keep='first')
    duplicates = raw.loc[duplicate_mask].copy()
    clean = raw.loc[~duplicate_mask].copy()
    clean['ShippingState'] = clean['ShippingState'].fillna('Unknown')
    clean['OrderDate'] = pd.to_datetime(clean['OrderDate'], format='%Y-%m-%d', errors='coerce')
    quantity = pd.to_numeric(clean['Quantity'], errors='coerce')
    price = pd.to_numeric(clean['UnitPrice'], errors='coerce')
    valid_quantity = quantity.notna() & np.isfinite(quantity) & (quantity % 1 == 0)
    # Int64 excludes numbers outside its representable range.
    valid_quantity &= (quantity >= -(2**63)) & (quantity < 2**63)
    valid_price = price.notna() & np.isfinite(price)
    reasons = pd.Series('', index=clean.index, dtype='string')
    reasons.loc[~valid_quantity] = 'Missing or invalid Quantity'
    reasons.loc[~valid_price] = reasons.loc[~valid_price].apply(
        lambda s: (s + '; ' if s else '') + 'Missing or invalid UnitPrice')
    rejected = raw.loc[clean.index[reasons.ne('')]].copy()
    rejected['RejectReasons'] = reasons.loc[rejected.index]
    clean['Quantity'] = quantity.where(valid_quantity).astype('Int64')
    clean['UnitPrice'] = price.where(valid_price)
    accepted = clean.loc[reasons.eq('')].copy()
    counts = dict(raw_rows=len(raw), duplicate_rows=len(duplicates),
                  unique_rows=len(clean), accepted_rows=len(accepted), rejected_rows=len(rejected))
    if counts['raw_rows'] != sum(counts[k] for k in ('duplicate_rows','accepted_rows','rejected_rows')):
        raise RuntimeError('Row reconciliation failed')
    return accepted, rejected, duplicates, counts


def run_pipeline(source, output):
    """Write to a new directory; refuse overwriting an earlier run."""
    source, output = Path(source), Path(output)
    source_bytes = source.read_bytes()
    import io
    raw = pd.read_csv(io.BytesIO(source_bytes))
    accepted, rejected, duplicates, counts = transform(raw)
    output.mkdir(parents=True, exist_ok=False)
    logger = logging.getLogger('retail_etl')
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(output / 'pipeline.log', mode='w')
    handler.setFormatter(logging.Formatter('%(levelname)s %(message)s'))
    logger.addHandler(handler)
    try:
        for name, frame in [('accepted', accepted), ('rejected', rejected), ('duplicates', duplicates)]:
            frame.to_csv(output / f'{name}.csv', index=False)
            frame.to_json(output / f'{name}.json', orient='records', date_format='iso', indent=2)
            if len(pd.read_csv(output / f'{name}.csv')) != len(frame):
                raise RuntimeError(f'{name} CSV row count mismatch')
            if len(json.loads((output / f'{name}.json').read_text())) != len(frame):
                raise RuntimeError(f'{name} JSON row count mismatch')
        report = {**counts, 'source_sha256': hashlib.sha256(source_bytes).hexdigest(),
                  'contract_version': '1.0', 'csv_json_counts_verified': True,
                  'accepted_missing_dates': int(accepted['OrderDate'].isna().sum()),
                  'accepted_missing_discounts': int(accepted['DiscountPct'].isna().sum())}
        # Completion marker: consumers should only use a run with this file.
        (output / 'run_summary.json').write_text(json.dumps(report, indent=2) + '\n')
        logger.info('Completed: %s', counts)
        return report
    except Exception:
        logger.exception('Run failed; outputs may be partial')
        raise
    finally:
        logger.removeHandler(handler)
        handler.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path('data/raw/retail_sales.csv'))
    parser.add_argument('--output', type=Path, default=Path('outputs/run-001'))
    args = parser.parse_args()
    try:
        report = run_pipeline(args.input, args.output)
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f'Pipeline failed: {error}\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
