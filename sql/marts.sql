-- Transform 2: the views Tableau and the alerts read. All KPI logic lives here, in SQL.
DROP SCHEMA IF EXISTS mart CASCADE;
CREATE SCHEMA mart;

-- Reporting window, defined once. Olist has only a handful of orders before 2017 and after Aug 2018.
-- snapshot = when the data was extracted: orders still undelivered by then, and past their promised date, are late.
CREATE VIEW mart.period AS
SELECT date '2017-01-01' AS start_date, date '2018-09-01' AS end_date,
       (SELECT max(greatest(purchased_at, approved_at, shipped_at, delivered_at)) FROM clean.orders)::date AS snapshot;

-- One row per order. Tableau aggregates from this grain, so every filter (date, state, category) works.
-- Flags are 1/0 (Postgres exports booleans as t/f, which Tableau reads as text); AVG of a flag is its rate.
CREATE VIEW mart.order_facts AS
WITH items AS (
  SELECT i.order_id, count(*) AS items, sum(i.price) AS item_value, sum(i.freight) AS freight,
         max(i.ship_by) AS ship_by, mode() WITHIN GROUP (ORDER BY p.category) AS category
  FROM clean.order_items i
  JOIN clean.products p USING (product_id)
  GROUP BY i.order_id
)
SELECT o.order_id, o.purchased_at::date AS purchase_date, o.status,
       o.customer_state AS state, s.state_name, s.region, i.category,
       i.items, i.item_value, i.freight,
       (o.status IN ('canceled', 'unavailable'))::int                         AS failed,
       (o.delivered_at IS NOT NULL)::int                                      AS delivered,
       round(extract(epoch FROM o.delivered_at - o.purchased_at) / 86400, 2)  AS delivery_days,
       (CASE WHEN o.delivered_at IS NOT NULL THEN o.delivered_at::date > o.promised_date
            WHEN o.status IN ('canceled', 'unavailable') THEN NULL  -- not a delivery
            WHEN o.promised_date < p.snapshot THEN true             -- never arrived, past its promised date
       END)::int                                                              AS late,
       greatest(o.delivered_at::date - o.promised_date, 0)                    AS days_late,  -- delivered orders only
       (o.shipped_at > i.ship_by)::int                                        AS seller_late,
       EXISTS (SELECT 1 FROM clean.holidays h
               WHERE h.day BETWEEN o.purchased_at::date AND o.promised_date)::int AS holiday_in_window,
       r.score AS review_score
FROM clean.orders o
CROSS JOIN mart.period p
JOIN clean.states s ON s.state = o.customer_state
LEFT JOIN items i USING (order_id)
LEFT JOIN clean.reviews r USING (order_id)
WHERE o.purchased_at >= p.start_date AND o.purchased_at < p.end_date;

-- The 8 dashboard KPIs, per state per month.
CREATE VIEW mart.kpi_monthly AS
SELECT date_trunc('month', purchase_date)::date             AS month, state, state_name, region,
       count(*)                                             AS orders,
       sum(failed)                                          AS failed_orders,
       round(avg(delivery_days), 2)                         AS avg_delivery_days,
       round(1 - avg(late), 4)                              AS on_time_rate,       -- orders that were due
       count(*) FILTER (WHERE late = 1)                     AS late_deliveries,
       round(avg(seller_late), 4)                           AS seller_late_rate,   -- shipped orders only
       round(avg(review_score), 2)                          AS avg_review,
       round(sum(freight) / nullif(sum(item_value + freight), 0), 4) AS freight_share
FROM mart.order_facts
GROUP BY 1, 2, 3, 4;

-- Supplier side: did each seller hand parcels to the carrier by the deadline?
CREATE VIEW mart.seller_performance AS
SELECT i.seller_id, se.state AS seller_state, date_trunc('month', o.purchased_at)::date AS month,
       count(*)                                          AS items_shipped,
       count(*) FILTER (WHERE o.shipped_at > i.ship_by)  AS late_handovers,
       round(avg(extract(epoch FROM o.shipped_at - i.ship_by) / 3600)
             FILTER (WHERE o.shipped_at > i.ship_by), 1) AS avg_hours_late,
       round(sum(i.price), 2)                            AS revenue
FROM clean.order_items i
JOIN clean.orders o USING (order_id)
JOIN clean.sellers se USING (seller_id)
CROSS JOIN mart.period p
WHERE o.shipped_at IS NOT NULL AND o.purchased_at >= p.start_date AND o.purchased_at < p.end_date
GROUP BY 1, 2, 3;

-- Alerts: what needs action in the latest month. Thresholds are the business targets.
CREATE VIEW mart.exceptions AS
WITH latest AS (SELECT max(month) AS month FROM mart.kpi_monthly)
SELECT k.month, 'state on-time rate below 90%' AS rule, k.state AS entity, k.on_time_rate AS value, k.orders AS volume
FROM mart.kpi_monthly k JOIN latest USING (month)
WHERE k.on_time_rate < 0.90 AND k.orders >= 30
UNION ALL
SELECT s.month, 'seller late-handover rate above 20%', s.seller_id, round(s.late_handovers::numeric / s.items_shipped, 4), s.items_shipped
FROM mart.seller_performance s JOIN latest USING (month)
WHERE s.items_shipped >= 10 AND s.late_handovers > 0.20 * s.items_shipped
ORDER BY rule, value;
