# Data dictionary and validation report

Errors: 0. Warnings: 2.

## Files

| File | Rows | Rows excluded | Duplicate rows | Unique SKUs | Unique distributors | Date range |
|---|---|---|---|---|---|---|
| weekly_sales.csv | 256 | 0 | 0 | 16 |  | 2026-W27 to 2026-W42 (2026-06-29 to 2026-10-18) |
| sku_master.csv | 16 | 0 | 0 | 16 | 4 |  |
| distributor_master.csv | 4 | 0 | 0 |  | 4 |  |
| current_inventory.csv | 16 | 0 | 0 | 16 |  | 2026-10-19 |
| calendar.csv | 24 | 0 | 0 |  |  | 2025-01 to 2026-12 |

## Join keys

- weekly_sales.SKU_ID, current_inventory.SKU_ID -> sku_master.SKU_ID
- sku_master.Distributor_ID -> distributor_master.Distributor_ID (one distributor per SKU; meaning undefined)
- month of each sales week (ISO Thursday) -> calendar.Year_Month

## Findings

| file | line | column | severity | check | value | message |
|---|---|---|---|---|---|---|
| distributor_master.csv | 4 | Region | warning | case_inconsistency | Karnataka | Case says Freshroots operates in Maharashtra and Goa; this region is outside that scope. |
| distributor_master.csv | 5 | Region | warning | case_inconsistency | Gujarat | Case says Freshroots operates in Maharashtra and Goa; this region is outside that scope. |
| sku_master.csv |  | Distributor_ID | info | ambiguous_definition |  | Each SKU maps to exactly one distributor. The case does not define this field; it is shown as 'mapped distributor' and is not used in any calculation. |
| weekly_sales.csv |  |  | info | granularity | SKU x week | Sales are aggregated per SKU; there is no distributor column, so distributor-level demand shifts cannot be analysed from this file. |
| weekly_sales.csv |  |  | info | sample_scale | 16 SKUs, 16 weeks | The case describes 400 SKUs and 3 years of history; this file is a sample. Backtest results are indicative only. |

## Data dictionary

| file | column | observed_type | missing | unique_values | example | description |
|---|---|---|---|---|---|---|
| weekly_sales.csv | SKU_ID | text | 0 | 16 | SKU001 | Product identifier; joins to sku_master.SKU_ID. |
| weekly_sales.csv | Week | iso_week | 0 | 16 | 2026-W27 | ISO week label (YYYY-Www, Monday-Sunday). One row per SKU per week. |
| weekly_sales.csv | Units_Sold | integer | 0 | 110 | 194 | Units sold in the week, aggregated across all distributors (no distributor column). |
| sku_master.csv | SKU_ID | text | 0 | 16 | SKU001 | Product identifier (primary key). |
| sku_master.csv | SKU_Name | text | 0 | 16 | Freshroots Mango Drink 200ml | Product description. |
| sku_master.csv | Category | text | 0 | 5 | Beverage | Product category. |
| sku_master.csv | Perishability | text | 0 | 2 | Low | Low or High. High = perishable SKU (Rule E applies). |
| sku_master.csv | Standard_Reorder_Qty | integer | 0 | 9 | 500 | Standard reorder quantity in units; base for Rule B (1.5x). |
| sku_master.csv | Unit_of_Measure | text | 0 | 1 | Units | Unit for quantities. |
| sku_master.csv | Distributor_ID | text | 0 | 4 | DIST001 | One distributor per SKU; joins to distributor_master. Meaning not defined in the case (treated as 'mapped distributor'). |
| distributor_master.csv | Distributor_ID | text | 0 | 4 | DIST001 | Distributor identifier (primary key). |
| distributor_master.csv | Distributor_Name | text | 0 | 4 | NutriFlow Distributors | Distributor name. |
| distributor_master.csv | Region | text | 0 | 3 | Maharashtra | State of operation. |
| distributor_master.csv | Status | text | 0 | 1 | Active | Account status. |
| current_inventory.csv | SKU_ID | text | 0 | 16 | SKU001 | Product identifier; joins to sku_master.SKU_ID. |
| current_inventory.csv | Location | text | 0 | 1 | Pune Central Warehouse | Stocking location. Stock is summed across locations per SKU. |
| current_inventory.csv | Units_On_Hand | integer | 0 | 14 | 900 | Units on hand at As_Of_Date. No expiry, in-transit or open-PO data. |
| current_inventory.csv | As_Of_Date | date | 0 | 1 | 2026-10-19 | Snapshot date (YYYY-MM-DD). Used as the analysis date. |
| calendar.csv | Year | integer | 0 | 2 | 2025 | Calendar year. |
| calendar.csv | Month | integer | 0 | 12 | 1 | Calendar month number (1-12). |
| calendar.csv | Year_Month | year_month | 0 | 24 | 2025-01 | YYYY-MM key; joins to the month of each sales week. |
| calendar.csv | Is_Festival_Month | boolean | 0 | 2 | FALSE | TRUE/FALSE. TRUE triggers Rule A (+25% demand uplift). |
