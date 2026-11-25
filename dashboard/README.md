# Tableau dashboard: build spec

## Current workbook

Open **[Supply_Chain_Performance.twbx](Supply_Chain_Performance.twbx)** in Tableau Public. It includes both Hyper extracts and the two cleaned CSV exports, so no PostgreSQL connection or original Olist download is needed to view it. Both dashboard tabs use a fixed 1100 × 660 desktop layout.

Published to Tableau Public on 25 November 2026:

- [Delivery overview](https://public.tableau.com/app/profile/sourav.gupta7998/viz/Supply_Chain_Performance/SupplyChainPerformance) · [PNG preview](dashboard.png)
- [Seller follow-up](https://public.tableau.com/app/profile/sourav.gupta7998/viz/Supply_Chain_Performance_seller/Sellerfollow-up) · [PNG preview](seller-follow-up.png)

The live dashboards are published as two workbooks. The downloadable local package contains both dashboard tabs.

Built and inspected in Tableau on 25 November 2026:

- **Supply Chain Performance:** four headline cards (orders, on-time rate, average delivery days, canceled/unavailable rate), a monthly volume/on-time trend, Brazil state map and color legend, and directly labeled customer-review bars on a fixed 0–5 scale.
- **Seller follow-up:** a separate full-period table of 15 sellers, with complete IDs, shipped-item counts and weighted late-handover rates. Keeping it separate avoids mixing full-period seller data with filtered order metrics.
- Clearer titles, consistent spacing, white panels on a pale background, readable category aliases and brief instructions. Supporting worksheets are hidden from the tab bar; all eight original KPI calculations remain in the editable workbook and can be unhidden for analysis.
- Baseline: 99,092 orders; 91.6% on time; 8,239 late deliveries; 1.2% failed; 12.5 average delivery days; 9.0% seller late handover; 4.09 average review; 14.2% freight share.
- Corrected `Failed %` from `AVG([late])` to `AVG([failed])`, removed the extra connection in the order source, set geographic context to Brazil, and made the monthly axis retain the year.
- Seller ranking is descending late-handover rate among sellers with at least 30 shipped items. All 15 rows were checked against independently aggregated CSV data.
- A state-selection action targets the order KPI cards, trend and review chart. Clearing selection resets the filter. The map and seller shortlist are excluded as targets; seller performance stays on the full reporting period.
- Purchase-date range, region and category controls share filters across all 12 order worksheets, including the KPI cards, trend, map and reviews. Region and category are single-value dropdowns with an `(All)` option. The seller source remains separate and full-period.

**Map action:** Sourav confirmed the map-click test was completed on 25 November 2026. This is user verification; automated chart-mark clicks were unavailable.

**Manual acceptance checks:** On 25 November 2026, Sourav confirmed the final region/category dropdown checks, reset to `(All)` with 99,092 orders, and map selection/clear checks were completed. These results are user-reported.

**Filter checks:** Editing the date control to end on 31 December 2017 returned 45,101 orders, matching the CSV. Separate test copies with preset filters returned 6,651 orders for South in 2017 and 348 for the audio category. Resetting the South copy's date control to 31 August 2018 returned 14,091. The filtered KPI cards and map rendered correctly; the seller shortlist retained its full-period ranking. The final package was reopened with all regions/categories and the full date range: 99,092 orders.

After the design update, the 2017 date test was repeated in Tableau and the complete 15-row seller table was inspected while that filter was active. Both dashboards were checked visually at desktop size. The pre-design workbook and live saved state are preserved under `Documents/My Tableau Repository/Workbooks/Backups/`.

**Published-view verification:** Both public views returned PNG renders successfully. The overview render shows the expected 99,092 orders, 91.6% on-time rate, 12.5 average delivery days and 1.2% canceled/unavailable rate. The seller render shows the complete 15-row ranking. The saved previews came from these public views and were visually inspected. Interactive filter/map acceptance checks above were performed before publishing; published interactions have not been repeated.

The workbook uses public Olist data, not employer data. Its metrics describe the January 2017–August 2018 reporting window and should not be substituted for employment results on a resume.

## Rebuild the package after an ETL refresh

From the repository root, using Python 3.12:

```bash
python -m pip install -r dashboard/requirements.txt
python dashboard/build_package.py
```

The script reads the workbook schema, checks each CSV header, regenerates the extracts, checks row counts and unique order IDs, and writes a portable `.twbx` with relative data references. It does not rerun the ETL. Close the workbook before rebuilding and reopen the package afterward. Do not save an old open workbook over a newly rebuilt package.

`Supply_Chain_Performance.twb` is the editable source. `Data/` holds generated extracts and is ignored by Git; the package embeds them. Keep a copy of the packaged workbook before making design changes.

## Original build recipe

This is the spec for the Tableau Public dashboard: data sources, calculated fields, sheets and layout. Tableau Public can't connect to Postgres, so it reads the CSVs that `etl.py` writes to `exports/`.

## 1. Data sources

1. Open Tableau Public and go to **Connect → Text file → `exports/order_facts.csv`**.
2. Check the field types on the Data Source page and fix any that are wrong:
   - `purchase_date` should be a **Date**.
   - `state_name` should be **Geographic Role → State/Province**.
   - `failed`, `delivered`, `late`, `seller_late` and `holiday_in_window` should be **Number (whole)**. They are 1/0 flags, so the average of one is its rate.
3. Add a second source with **Data → New Data Source → Text file → `exports/seller_performance.csv`**. Check that `month` is a Date.
   - Keep it a separate source. Don't drag it onto the `order_facts` canvas: the two files share no key, so Tableau can't relate them, and every sheet fails with error F3ADC07B ("Multiple Connections").

## 2. Calculated fields (on order_facts)

Create each field with **Analysis → Create Calculated Field**.

| Name | Formula | Format |
|---|---|---|
| Orders | `COUNTD([Order Id])` | number |
| On-time % | `1 - AVG([Late])` | % (1 decimal) |
| Late deliveries | `SUM([Late])` | number |
| Failed % | `AVG([Failed])` | % (1 decimal) |
| Avg delivery days | `AVG([Delivery Days])` | 1 decimal |
| Seller late-handover % | `AVG([Seller Late])` | % (1 decimal) |
| Avg review | `AVG([Review Score])` | 2 decimals |
| Freight share | `SUM([Freight]) / (SUM([Item Value]) + SUM([Freight]))` | % (1 decimal) |
| Delivery outcome | `IF [Late] = 1 THEN "Late" ELSEIF [Late] = 0 THEN "On time" END` | |

On `seller_performance`, add one more: **Late-handover rate** = `SUM([Late Handovers]) / SUM([Items Shipped])`.

## 3. Sheets

1. **KPIs**
   - Drag **Measure Names** to Columns and **Measure Values** to Text.
   - Keep only the 8 KPI fields in the Measure Values card.
   - Increase the font size, then hide the column title.
2. **Monthly trend**
   - Put `purchase_date` on Columns as continuous **MONTH**.
   - Put `Orders` on Rows, set the mark type to Bar, and add `On-time %` next to it on Rows.
   - Right-click `On-time %` → **Dual Axis**, and set its mark type to Line. The dips in Nov 2017 and Feb–Mar 2018 should show.
3. **Map**
   - Double-click `state_name`.
   - If the states land outside Brazil, go to **Map → Edit Locations → Country/Region: Brazil**.
   - Put `On-time %` on Color, using a red-to-green diverging palette centred at 0.9.
   - Add `Orders` and `Avg delivery days` to the Tooltip.
4. **Late deliveries vs reviews**
   - Put `Delivery outcome` on Rows and `Avg review` on Columns.
   - Filter out Null.
   - Expect about 4.3 stars for on-time orders and 2.2 for late ones.
5. **Sellers to chase** (uses the `seller_performance` source)
   - Put `seller_id` and `seller_state` on Rows, and `Late-handover rate` and `SUM(Items Shipped)` as text.
   - Filter `SUM(Items Shipped)` to at least 30 and sort by rate, descending.
   - Use a **Top 15** filter on `seller_id`.

## 4. Dashboard

1. Create a **New Dashboard** with a fixed size of 1200 × 960.
2. Lay it out like this:
   - **Top:** KPIs, full width.
   - **Middle:** Monthly trend on the left (60%) and Map on the right (40%).
   - **Bottom:** Late deliveries vs reviews on the left and Sellers to chase on the right.
3. Add filters from the Monthly trend sheet: `purchase_date` as a range, `region` and `category`. For each one, choose **Apply to Worksheets → All Using This Data Source**.
4. Make the map act as a filter: click the funnel icon on the Map sheet, so clicking a state filters the other sheets.
5. Title it **Supply Chain Performance: Olist, Jan 2017 – Aug 2018**.

## 5. Publish

1. Go to **File → Save to Tableau Public As…** and sign in to your free Tableau Public account.
2. Paste the public link into the main README.
3. Export a screenshot with **Dashboard → Export Image**, saved as `dashboard/dashboard.png`.

Tableau Public only refreshes data automatically from Google Sheets. With the CSVs, re-publish after each ETL run. In a company setup, Tableau Server or Cloud would connect to Postgres directly and refresh on a schedule.
