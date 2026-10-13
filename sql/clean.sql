-- Transform 1: typed, de-duplicated tables built from raw.* (raw is all text, exactly as in the CSVs).
DROP SCHEMA IF EXISTS clean CASCADE;
CREATE SCHEMA clean;

CREATE TABLE clean.states (state char(2) PRIMARY KEY, state_name text NOT NULL, region text NOT NULL);
INSERT INTO clean.states VALUES
  ('AC','Acre','North'), ('AP','Amapá','North'), ('AM','Amazonas','North'), ('PA','Pará','North'),
  ('RO','Rondônia','North'), ('RR','Roraima','North'), ('TO','Tocantins','North'),
  ('AL','Alagoas','Northeast'), ('BA','Bahia','Northeast'), ('CE','Ceará','Northeast'), ('MA','Maranhão','Northeast'),
  ('PB','Paraíba','Northeast'), ('PE','Pernambuco','Northeast'), ('PI','Piauí','Northeast'),
  ('RN','Rio Grande do Norte','Northeast'), ('SE','Sergipe','Northeast'),
  ('DF','Distrito Federal','Central-West'), ('GO','Goiás','Central-West'), ('MT','Mato Grosso','Central-West'),
  ('MS','Mato Grosso do Sul','Central-West'),
  ('ES','Espírito Santo','Southeast'), ('MG','Minas Gerais','Southeast'), ('RJ','Rio de Janeiro','Southeast'),
  ('SP','São Paulo','Southeast'),
  ('PR','Paraná','South'), ('RS','Rio Grande do Sul','South'), ('SC','Santa Catarina','South');

-- Constraints below are the main data-quality gate: if the source breaks a rule, the load fails.
CREATE TABLE clean.customers AS
SELECT customer_id, customer_unique_id, customer_city AS city, customer_state AS state
FROM raw.customers;
ALTER TABLE clean.customers ADD PRIMARY KEY (customer_id), ADD FOREIGN KEY (state) REFERENCES clean.states;

CREATE TABLE clean.sellers AS
SELECT seller_id, seller_city AS city, seller_state AS state
FROM raw.sellers;
ALTER TABLE clean.sellers ADD PRIMARY KEY (seller_id), ADD FOREIGN KEY (state) REFERENCES clean.states;

-- A few Portuguese categories are missing from the translation file; keep the Portuguese name rather than drop them.
CREATE TABLE clean.products AS
SELECT p.product_id, coalesce(t.product_category_name_english, p.product_category_name, 'unknown') AS category
FROM raw.products p
LEFT JOIN raw.product_category_name_translation t USING (product_category_name);
ALTER TABLE clean.products ADD PRIMARY KEY (product_id);

-- Some carrier handover dates fall before the purchase or after the delivery. They can't be right,
-- so they're treated as unknown (NULL) instead of skewing the seller-delay KPIs.
CREATE TABLE clean.orders AS
SELECT order_id, customer_id, customer_state, status, purchased_at, approved_at,
       CASE WHEN shipped_at BETWEEN purchased_at AND coalesce(delivered_at, 'infinity') THEN shipped_at END AS shipped_at,
       delivered_at, promised_date
FROM (
  SELECT o.order_id, o.customer_id, c.state AS customer_state, o.order_status AS status,
         o.order_purchase_timestamp::timestamp      AS purchased_at,
         o.order_approved_at::timestamp             AS approved_at,
         o.order_delivered_carrier_date::timestamp  AS shipped_at,    -- seller handed the parcel to the carrier
         o.order_delivered_customer_date::timestamp AS delivered_at,
         o.order_estimated_delivery_date::date      AS promised_date  -- delivery date shown to the customer
  FROM raw.orders o
  JOIN clean.customers c USING (customer_id)
) o;
ALTER TABLE clean.orders
  ADD PRIMARY KEY (order_id),
  ADD FOREIGN KEY (customer_id) REFERENCES clean.customers,
  ADD CHECK (delivered_at >= purchased_at),
  ADD CHECK (shipped_at BETWEEN purchased_at AND delivered_at);

CREATE TABLE clean.order_items AS
SELECT order_id, order_item_id::int AS item_no, product_id, seller_id,
       shipping_limit_date::timestamp AS ship_by,  -- deadline for the seller to hand over to the carrier
       price::numeric, freight_value::numeric AS freight
FROM raw.order_items;
ALTER TABLE clean.order_items
  ADD PRIMARY KEY (order_id, item_no),
  ADD FOREIGN KEY (order_id) REFERENCES clean.orders,
  ADD FOREIGN KEY (product_id) REFERENCES clean.products,
  ADD FOREIGN KEY (seller_id) REFERENCES clean.sellers,
  ADD CHECK (price >= 0 AND freight >= 0);

-- The raw file has several reviews for some orders; keep the most recent one per order.
CREATE TABLE clean.reviews AS
SELECT DISTINCT ON (order_id) order_id, review_score::int AS score
FROM raw.order_reviews
ORDER BY order_id, review_answer_timestamp::timestamp DESC;
ALTER TABLE clean.reviews
  ADD PRIMARY KEY (order_id),
  ADD FOREIGN KEY (order_id) REFERENCES clean.orders,
  ADD CHECK (score BETWEEN 1 AND 5);

CREATE TABLE clean.holidays AS
SELECT DISTINCT date::date AS day, name FROM raw.holidays;
