# Metabase Analytics

Metabase is included in the Docker setup to address analytics needs
(see [#50](https://github.com/vokomokum/voko/issues/50) and
[#413](https://github.com/vokomokum/voko/issues/413)).

## Starting Metabase

```bash
# Start alongside all other services (recommended)
make docker-up

# Or start only Metabase (requires db to already be running)
make metabase-up
```

Metabase is available at **http://localhost:3000**. First startup takes ~30 seconds.

## First-time setup

1. Open http://localhost:3000 and complete the welcome wizard.
2. When asked to add a database, choose **PostgreSQL** and fill in:

   | Field    | Value      |
   |----------|------------|
   | Host     | `db`       |
   | Port     | `5432`     |
   | Database | `postgres` |
   | Username | `postgres` |
   | Password | `postgres` |

3. Save and you're ready to start building questions.

## Suggested questions

The queries below map directly to the open issues.

### Issue #50 — Member & round analytics

**Orders per round (trend)**
```sql
SELECT
    r.id                            AS round,
    r.open_for_orders::date         AS opened,
    COUNT(o.id)                     AS paid_orders
FROM ordering_orderround r
LEFT JOIN ordering_order o ON o.order_round_id = r.id AND o.paid = true
GROUP BY r.id, r.open_for_orders
ORDER BY r.open_for_orders;
```

**Active vs sleeping members**
```sql
SELECT
    CASE WHEN is_asleep THEN 'sleeping' ELSE 'active' END AS status,
    COUNT(*) AS members
FROM accounts_vokouser
WHERE is_active = true OR is_asleep = true
GROUP BY is_asleep;
```

**Registration funnel (registered → confirmed → active)**
```sql
SELECT
    COUNT(*)                                            AS registered,
    COUNT(*) FILTER (WHERE ec.is_confirmed = true)      AS email_confirmed,
    COUNT(*) FILTER (WHERE u.can_activate = true)       AS can_activate,
    COUNT(*) FILTER (WHERE u.is_active = true)          AS activated
FROM accounts_vokouser u
LEFT JOIN accounts_emailconfirmation ec ON ec.user_id = u.id;
```

**Markup history per round**
```sql
SELECT
    id                        AS round,
    open_for_orders::date     AS opened,
    markup_percentage
FROM ordering_orderround
ORDER BY open_for_orders;
```

**Corrections per round**
```sql
SELECT
    r.id                    AS round,
    r.open_for_orders::date AS opened,
    COUNT(c.id)             AS corrections
FROM ordering_orderround r
LEFT JOIN ordering_order o     ON o.order_round_id = r.id AND o.paid = true
LEFT JOIN ordering_orderproduct op ON op.order_id = o.id
LEFT JOIN ordering_orderproductcorrection c ON c.order_product_id = op.id
GROUP BY r.id, r.open_for_orders
ORDER BY r.open_for_orders;
```

**Suppliers per round**
```sql
SELECT
    r.id                    AS round,
    r.open_for_orders::date AS opened,
    COUNT(DISTINCT p.supplier_id) AS suppliers
FROM ordering_orderround r
LEFT JOIN ordering_product p ON p.order_round_id = r.id
GROUP BY r.id, r.open_for_orders
ORDER BY r.open_for_orders;
```

**% of active members who ordered per round**
```sql
SELECT
    r.id                        AS round,
    r.open_for_orders::date     AS opened,
    COUNT(DISTINCT o.user_id)   AS members_ordered,
    (SELECT COUNT(*) FROM accounts_vokouser WHERE is_active = true AND is_asleep = false) AS active_members,
    ROUND(
        100.0 * COUNT(DISTINCT o.user_id)
        / NULLIF((SELECT COUNT(*) FROM accounts_vokouser WHERE is_active = true AND is_asleep = false), 0),
        1
    ) AS pct_ordering
FROM ordering_orderround r
LEFT JOIN ordering_order o ON o.order_round_id = r.id AND o.paid = true
GROUP BY r.id, r.open_for_orders
ORDER BY r.open_for_orders;
```

---

### Issue #413 — Sales reports (volume sold per period)

**Units sold per product per month**
```sql
SELECT
    DATE_TRUNC('month', r.collect_datetime) AS month,
    s.name                                  AS supplier,
    p.name                                  AS product,
    SUM(op.amount)                          AS units_sold,
    SUM(op.amount * op.base_price)          AS revenue_excl_markup,
    SUM(op.amount * op.retail_price)        AS revenue_incl_markup
FROM ordering_orderproduct op
JOIN ordering_order o      ON o.id = op.order_id AND o.paid = true
JOIN ordering_orderround r ON r.id = o.order_round_id
JOIN ordering_product p    ON p.id = op.product_id
JOIN ordering_supplier s   ON s.id = p.supplier_id
GROUP BY month, supplier, product
ORDER BY month DESC, supplier, product;
```

**Revenue per supplier per year**
```sql
SELECT
    DATE_TRUNC('year', r.collect_datetime)  AS year,
    s.name                                  AS supplier,
    SUM(op.amount * op.base_price)          AS cost_price_total,
    SUM(op.amount * op.retail_price)        AS retail_total
FROM ordering_orderproduct op
JOIN ordering_order o      ON o.id = op.order_id AND o.paid = true
JOIN ordering_orderround r ON r.id = o.order_round_id
JOIN ordering_product p    ON p.id = op.product_id
JOIN ordering_supplier s   ON s.id = p.supplier_id
GROUP BY year, supplier
ORDER BY year DESC, retail_total DESC;
```

**Total revenue per month (for bar/line chart)**
```sql
SELECT
    DATE_TRUNC('month', r.collect_datetime) AS month,
    SUM(op.amount * op.retail_price)        AS total_revenue,
    SUM(op.amount * (op.retail_price - op.base_price)) AS total_markup_earned
FROM ordering_orderproduct op
JOIN ordering_order o      ON o.id = op.order_id AND o.paid = true
JOIN ordering_orderround r ON r.id = o.order_round_id
GROUP BY month
ORDER BY month;
```
