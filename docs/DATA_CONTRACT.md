# Data contract — version 1.0

Input: UTF-8 comma-separated CSV with a header and the following columns in this order. The source is synthetic; each row is treated as a retail record, not a guaranteed unique order.

| Column | Processing rule |
|---|---|
| OrderID | Retained; uniqueness is not asserted |
| OrderDate | Parse YYYY-MM-DD; unparseable becomes missing and is counted in accepted output |
| CustomerID | Retained |
| ProductID | Retained |
| ProductCategory | Retained |
| ProductName | Retained |
| Quantity | Numeric, finite, whole number in signed Int64 range; otherwise reject |
| UnitPrice | Numeric and finite; otherwise reject |
| DiscountPct | Retained, including missing; no zero imputation or range gate |
| ShippingState | Missing becomes Unknown in accepted records |
| PaymentMethod | Retained |
| SalesChannel | Retained |

Exact duplicate rows are identified across the parsed source columns before transformations. The first is processed; extra copies are exported. This is parsed-value equality, not byte-level CSV equality. pandas' default missing-value interpretation applies.

Rejections preserve parsed source values and append `RejectReasons`, containing all applicable quantity/price failures. CSV does not retain pandas dtypes, and default parsing may change numeric textual formatting. The original source remains the definitive evidence.

Zero/negative quantity and price are allowed by this baseline. These may represent returns or data errors; business requirements must determine the policy. No revenue metric is generated. Missing discounts are unknown, not 0%.
