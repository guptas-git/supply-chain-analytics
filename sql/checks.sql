-- Rules the table constraints in clean.sql can't express. Each query returns the rows that break the rule.

-- order_facts has exactly one row per order in the reporting window
SELECT * FROM (
  SELECT (SELECT count(*) FROM clean.orders o, mart.period p
          WHERE o.purchased_at >= p.start_date AND o.purchased_at < p.end_date) AS orders,
         count(*) AS fact_rows, count(DISTINCT order_id) AS fact_orders
  FROM mart.order_facts
) t
WHERE NOT (orders = fact_rows AND fact_rows = fact_orders);

-- every month in the reporting window has orders (a gap means a partial load)
SELECT m::date AS missing_month
FROM mart.period, generate_series(start_date, end_date - 1, interval '1 month') m
WHERE m::date NOT IN (SELECT month FROM mart.kpi_monthly);

-- the holiday API returned national holidays
SELECT count(*) AS holidays FROM clean.holidays HAVING count(*) < 10;
