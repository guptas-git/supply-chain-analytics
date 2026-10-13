# Tableau dashboard: build spec

This is the spec for the Tableau Public dashboard: data sources, calculated fields, sheets and layout. Tableau Public can't connect to Postgres, so it reads the CSVs that `etl.py` writes to `exports/`.

## 1. Data sources

1. Open Tableau Public and go to **Connect → Text file → `exports/order_facts.csv`**.
2. Check the field types on the Data Source page and fix any that are wrong:
   - `purchase_date` should be a **Date**.
   - `state_name` should be **Geographic Role → State/Province**.
   - `failed`, `delivered`, `late`, `seller_late` and `holiday_in_window` should be **Number (whole)**. They are 1/0 flags, so the average of one is its rate.
3. Add a second source with **Data → New Data Source → Text file → `exports/seller_performance.csv`**. Check that `month` is a Date.

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

1. Create a **New Dashboard** with a fixed size of 1200 × 900.
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
