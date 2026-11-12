# Executive Memo: Trade Spend Diagnostic

**Cinderhaven Provisions | Trailing 12 Months**

---

## The Finding

Structural trade — the negotiated rate card — cost $3,177,051 on
$32,323,139.62 of trailing-52-week scan revenue (2025-01-04 to 2025-12-27): 9.8%. That number is
known, budgeted, and visible to everyone who signed the contracts.
All-in trade cost is 10.9%. The 1.1-point gap between the two is
$343,281 a year in operational waste: 4,772 deduction line items,
spread across eight categories, that appeared in no budget and no
report until the infrastructure to measure them was built.

The shape of the waste is the finding. Six of the eight categories —
spoilage, pricing errors, damaged goods, slotting, pallet fines,
label fines — each land between $48,861 and $53,664. The largest is
15.6% of the total. There is no villain category to fire, no single
contract to renegotiate, no one retailer program driving the number.
Waste this evenly distributed is a process problem: the deduction
pipeline leaks a little in every category because no step in it
verifies anything.

## Where the Money Goes

| Category | Events | Annual Cost | Addressable? |
|----------|-------:|------------:|:------------:|
| Spoilage claims | 546 | $53,664 | Yes |
| Pricing errors | 547 | $53,224 | Yes |
| Damaged goods | 543 | $53,169 | Yes |
| Slotting fees | 532 | $51,879 | No |
| Pallet fines | 580 | $51,565 | Yes |
| Label fines | 532 | $48,861 | Yes |
| Short-ship charges | 1,406 | $28,053 | Yes |
| Late delivery penalties | 86 | $2,865 | Yes |
| **Total operational waste** | **4,772** | **$343,281** | |
| **Addressable portion** | | **$291,402** | |

*Rows are rounded to the dollar; totals are computed on unrounded
figures.*

Two rows break the even pattern, in opposite directions. Short-ship
is high-frequency, low-dollar: 1,406 events — 29% of all waste
events — averaging $20 apiece. Nobody should dispute a $20 charge by
hand; short-ship is a case for automated matching against shipment
records, not analyst hours. Late delivery is noise: $2,865 across 86
events. Ignore it. Slotting sits outside the addressable total
because it is the price of shelf placement — a cost to negotiate at
contract time, not to dispute at remittance time.

## Promotions Billed Against No Calendar

521 promo billbacks totaling $50,055 across three years of
deduction history reference promotions that do not appear in
Cinderhaven's promotion calendar. The remaining 1,029 billbacks
($95,027) fall inside a promotion window and are accounted for. In
the trailing year, 513 of 540 promo billbacks ($49,315) lack a
matching calendar entry — the promotion calendar's last entry ends
2024-11-03 and no matching window extends past early February 2025.
Either retailers are billing for promotional activity that never
ran, or the calendar stopped being maintained — the data cannot say
which. Either way, Cinderhaven currently pays nearly every recent
promotional invoice without a document to check it against.

## Recovery Works — It Is Aimed at Too Little

Cinderhaven has filed 5,247 disputes covering $382,579 in
deductions and recovered $160,161: 41.9% of disputed dollars, and
49.7% on the disputes that have closed (1,411 won, 1,478 partially
recovered, 1,509 lost, 849 still pending). The win rate is not the
problem. Coverage is. Of the trailing year's $343,281 in waste, only
$109,726 — 32% — was ever disputed. And the average disputed
deduction is $73, which means the dispute effort spends itself on
exactly the small-dollar noise that should be automated, while
two-thirds of the waste never enters the process at all.

## Three Things to Do Monday Morning

1. **Cross-check the physical-handling claims against shipping
   records.** Spoilage, damaged goods, and pallet fines total
   $158,398. Match each claim to its BOL, carrier SLA, and receiving
   log. Where the retailer's claim contradicts the shipment record,
   dispute it — at 41.9 cents recovered per disputed dollar, this is
   the highest-yield hour an analyst can spend. Where the record
   confirms the claim, the fix is in the warehouse, not the dispute
   queue.

2. **Stop the self-inflicted categories at the source.** Pricing
   errors ($53,224) and label fines ($48,861) — $102,085 combined —
   are failures on Cinderhaven's side of the ledger: price files out
   of sync with retailer portals, labels shipped against stale
   specs. Pre-ship QC and a price-file reconciliation cadence cost
   less than the fines.

3. **Automate the small stuff and rebuild the promo calendar.** Set
   a dollar threshold below which short-ship charges are
   auto-matched to shipment records and either batch-disputed or
   written off — 1,406 manual $20 decisions is a payroll problem
   masquerading as a recovery program. And restore the promotion
   calendar as a control document, so next year's promo billbacks
   ($49,315 this year, nearly all of them unmatchable) have something
   to be checked against.

## The Bottom Line

The rate card is not leaking; the process around it is. $343,281 a
year exits through eight small holes, six of them nearly identical
in size, none of them large enough to have earned anyone's
attention. The dispute machinery already returns 42 cents on every
dollar it touches — but it touches less than a third of the waste,
and mostly the smallest pieces. The diagnostic quantifies the leak,
category by category. Closing it is verification work, not a single
decision.

---

*Full methodology, retailer-level detail, and the complete deduction
ledger are in the accompanying Excel workbook. Derivations and
rebuttal guidance for every headline number are in DEFENSIBILITY.md.*
