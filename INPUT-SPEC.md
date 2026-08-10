# Trade-Spend Data Diagnostic — Client Data Input Specification

This tool connects directly to a client's **data warehouse** (the reference
connection pattern for the portfolio — see `warehouse_adapter.py`). Every table
and column name is declared in `engagement.yml`'s `warehouse:` block; nothing is
hardcoded. Rows pulled from the warehouse go through the **same**
`lailara_engagement` POS specs and required declarations as the CSV client mode
(via `read_records`), so a mislabeled week grid or an unlabeled dollar basis is
caught identically whether the data arrives as a file or a cursor.

## Warehouse connection (`engagement.yml` → `warehouse:`)
```yaml
warehouse:
  kind: sqlite                 # any DB-API 2.0 source works the same way
  path: /path/to/warehouse.db  # (or a DSN for a networked warehouse)
  tables:
    scans: <your scan-movement table>
    deductions: <your deduction-ledger table>
  columns:
    scans:      # canonical -> your column
      store_id: "..."
      sku: "..."
      week_ending: "..."
      units_sold: "..."
      dollars_sold: "..."
    deductions:
      deduction_id: "..."
      deduction_type: "..."
      amount: "..."
      deduction_date: "..."
```

## §Scans — weekly POS scan movement (required table)
| Canonical | Type | Required | Used for |
|---|---|---|---|
| `store_id` | identifier | **required** | grain |
| `sku` | identifier | **required** | grain |
| `week_ending` | date | **required** | trailing-52-week window; validated on the declared weekday |
| `units_sold` | number ≥ 0 | **required** | volume |
| `dollars_sold` | number ≥ 0 | **required** | trailing-52-week revenue (basis = `scan_basis`) |

## §Deductions — the deduction ledger (required table)
| Canonical | Type | Required | Used for |
|---|---|---|---|
| `deduction_id` | identifier (unique) | **required** | ledger key |
| `deduction_type` | string | **required** | excludes `promo_billback` from operational waste |
| `amount` | number ≥ 0 | **required** | operational-waste dollars |
| `deduction_date` | date | **required** | trailing-365-day window |

## Required declarations (`basis:`)
- **`week_convention`** — validates every `week_ending` weekday (shared contract).
- **`scan_basis`** — `retail_scan` | `wholesale`; the revenue basis, carried into
  the provenance footer and printed next to the figure.

## Output
A branded, provenance-footed **Warehouse Trade-Spend Readiness** summary
(trailing-52-week revenue, operational-waste rate) — or a **Data Readiness
Report** naming exactly which mapped column is missing or mistyped. Structural
trade and promo efficacy extend the same connector by adding their rate-table
maps to `warehouse.columns`.
