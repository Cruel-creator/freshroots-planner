# Rule definitions and prototype assumptions (rules-v0.1.0-prototype)

## Documented rules (from the case)

- **A. Festival uplift**: in festival months (calendar.csv; October, November, March) the 12-week average weekly demand is multiplied by 1.25 once, before any cover threshold is checked.
- **B. High demand**: average of the latest 4 complete weeks more than 20% above the average of the latest 12 complete weeks (the 12 include the 4) -> reorder 1.5x Standard_Reorder_Qty.
- **C. Stockout risk**: weeks of cover below 6 -> reorder now (standard quantity, 1.5x if also high demand).
- **D. Overstock risk**: weeks of cover above 14 -> pause next order.
- **E. Perishables** (Perishability = High): below 3 weeks -> replenish; above 4 -> overstock; 3-4 -> within target.

Weeks of cover = Units_On_Hand (summed across locations) / festival-adjusted weekly demand. Values exactly on a threshold do not trigger it.

## Prototype assumptions (not approved Freshroots policy)

- The analysis date is the inventory As_Of_Date; the planning month is that date's month.
- A week belongs to the month of its Thursday (ISO convention).
- Perishable windows replace the 6/14-week windows for perishable SKUs (configurable).
- Missing sales weeks are not treated as zero; a 4+ week partial average is used for cover only and flagged.
- All on-hand stock is treated as usable (no expiry data).
- Rule priority:
  - 1. Data blocker: Cover or perishability cannot be determined -> planner decides; no quantity.
  - 2. Demand vs stock conflict: High demand together with any overstock flag -> planner decides; no quantity.
  - 3. Perishable safety: Perishable SKUs use the 3-4 week window. An order that would push cover above 4 weeks -> planner decides.
  - 4. Stockout risk: Below 6 weeks -> reorder now (1.5x standard quantity if also high demand).
  - 5. High demand: More than 20% above baseline with cover 6-14 weeks -> reorder 1.5x standard quantity.
  - 6. Overstock risk: Above 14 weeks -> pause next order.
  - 7. No action: All checks within thresholds.
- Operations signals (Option C): drop of more than 15% vs the previous 4-week average or week on week, spike of more than 25%. Open signals block procurement approval for that SKU until acknowledged.

## Unresolved business questions

- Does Rule B's 1.5x replace the standard order or add to it? (Prototype: the order quantity is 1.5x standard.)
- Which rule wins when high demand and overstock both trigger? (Prototype: planner decides, no quantity.)
- Do perishable windows replace the 6/14-week windows? (Prototype: yes, configurable.)
- Festival uplift: should it apply when the baseline window already contains festival weeks? (Prototype: applied once, noted.)
- What does Distributor_ID in the SKU master mean, given 1,200 distributors per the case?
- Lead times, open purchase orders, in-transit stock and shelf life are not in the data.
- Two mapped distributors are in Karnataka and Gujarat, outside the case's Maharashtra and Goa scope.
