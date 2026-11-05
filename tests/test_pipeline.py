import json
from pathlib import Path
import tempfile
import unittest

import pandas as pd
from retail_etl.pipeline import transform, run_pipeline

SOURCE = Path(__file__).resolve().parents[1] / 'data/raw/retail_sales.csv'


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.raw = pd.read_csv(SOURCE)

    def test_sample_reconciles(self):
        accepted, rejected, duplicates, counts = transform(self.raw)
        self.assertEqual(counts, dict(raw_rows=58, duplicate_rows=2, unique_rows=56,
                                     accepted_rows=53, rejected_rows=3))
        self.assertEqual(set(rejected.OrderID), {10046, 10012, 10038})

    def test_unknown_discount_preserved(self):
        accepted, *_ = transform(self.raw)
        self.assertTrue(accepted.loc[accepted.OrderID.eq(10028), 'DiscountPct'].isna().all())

    def test_shipping_unknown(self):
        accepted, *_ = transform(self.raw)
        self.assertEqual(accepted.loc[accepted.OrderID.eq(10049), 'ShippingState'].iloc[0], 'Unknown')

    def test_all_reasons_and_raw_evidence(self):
        row = self.raw.iloc[[0]].copy()
        row['Quantity'], row['UnitPrice'] = 'bad', 'bad'
        accepted, rejected, *_ = transform(row)
        self.assertEqual(len(accepted), 0)
        self.assertEqual(rejected.iloc[0]['UnitPrice'], 'bad')
        self.assertIn('; ', rejected.iloc[0]['RejectReasons'])

    def test_fractional_and_nonfinite_quantity_rejected(self):
        for value in [1.5, float('inf'), 2**63]:
            row = self.raw.iloc[[0]].copy(); row['Quantity'] = value
            self.assertEqual(len(transform(row)[1]), 1)

    def test_nonfinite_price_rejected(self):
        row = self.raw.iloc[[0]].copy(); row['UnitPrice'] = float('inf')
        self.assertEqual(len(transform(row)[1]), 1)

    def test_invalid_date_is_flagged_not_rejected(self):
        row = self.raw.iloc[[0]].copy(); row['OrderDate'] = 'invalid'
        accepted, rejected, *_ = transform(row)
        self.assertEqual(len(rejected), 0)
        self.assertTrue(accepted.OrderDate.isna().all())

    def test_schema_mismatch_fails(self):
        with self.assertRaises(ValueError):
            transform(self.raw.drop(columns=['Quantity']))

    def test_empty_input(self):
        self.assertEqual(transform(self.raw.iloc[:0])[3]['accepted_rows'], 0)

    def test_repeatable_exports_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            a, b = Path(directory)/'a', Path(directory)/'b'
            run_pipeline(SOURCE, a); run_pipeline(SOURCE, b)
            for name in ['accepted.csv','accepted.json','rejected.csv','rejected.json',
                         'duplicates.csv','duplicates.json','run_summary.json']:
                self.assertEqual((a/name).read_bytes(), (b/name).read_bytes())
            self.assertTrue(json.loads((a/'run_summary.json').read_text())['csv_json_counts_verified'])
            with self.assertRaises(FileExistsError):
                run_pipeline(SOURCE, a)


if __name__ == '__main__':
    unittest.main()
