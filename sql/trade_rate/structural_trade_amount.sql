-- ============================================
-- structural_trade_amount.sql
-- ============================================
-- Question: What is the total structural (planned) trade spend
--           in dollars, broken out by retailer?
-- Tables:   scan_data, stores, sku_costs
-- Output:   retailer, channel_revenue, trade_rate, structural_trade_dollars
-- Params:   :oldest_week — the 52nd-most-recent distinct
--           week_ending from trailing_52_weeks.sql
-- Notes:    Gap query — this calculation was done in Python by
--           pairing revenue_by_retailer results with channel
--           trade rates. This query does it in pure SQL.
--           Locked number (workbook): structural trade =
--           $3,177,051 (9.8% of revenue). Same channel mapping
--           as the workbook, so both return the same total.
--           Channel mapping: Walmart, Costco, Whole Foods, Sprouts,
--           Kroger, UNFI, DTC, KeHE each have their own rate column;
--           all other retailers use trade_spend_pct_regional.
-- ============================================

WITH channel_revenue AS (
    SELECT s.retailer,
           SUM(sd.dollars_sold) AS revenue
    FROM scan_data sd
    JOIN stores s ON sd.store_id = s.store_id
    WHERE sd.week_ending >= :oldest_week
    GROUP BY s.retailer
),
channel_rates AS (
    SELECT
        AVG(trade_spend_pct_walmart)     AS rate_walmart,
        AVG(trade_spend_pct_costco)      AS rate_costco,
        AVG(trade_spend_pct_whole_foods) AS rate_whole_foods,
        AVG(trade_spend_pct_sprouts)     AS rate_sprouts,
        AVG(trade_spend_pct_kroger)      AS rate_kroger,
        AVG(trade_spend_pct_unfi)        AS rate_unfi,
        AVG(trade_spend_pct_dtc)         AS rate_dtc,
        AVG(trade_spend_pct_kehe)        AS rate_kehe,
        AVG(trade_spend_pct_regional)    AS rate_regional
    FROM sku_costs
)
SELECT
    cr.retailer,
    cr.revenue AS channel_revenue,
    CASE cr.retailer
        WHEN 'Walmart'     THEN rates.rate_walmart
        WHEN 'Costco'      THEN rates.rate_costco
        WHEN 'Whole Foods' THEN rates.rate_whole_foods
        WHEN 'Sprouts'     THEN rates.rate_sprouts
        WHEN 'Kroger'      THEN rates.rate_kroger
        WHEN 'UNFI'        THEN rates.rate_unfi
        WHEN 'DTC'         THEN rates.rate_dtc
        WHEN 'KeHE'        THEN rates.rate_kehe
        ELSE rates.rate_regional
    END AS trade_rate,
    cr.revenue * CASE cr.retailer
        WHEN 'Walmart'     THEN rates.rate_walmart
        WHEN 'Costco'      THEN rates.rate_costco
        WHEN 'Whole Foods' THEN rates.rate_whole_foods
        WHEN 'Sprouts'     THEN rates.rate_sprouts
        WHEN 'Kroger'      THEN rates.rate_kroger
        WHEN 'UNFI'        THEN rates.rate_unfi
        WHEN 'DTC'         THEN rates.rate_dtc
        WHEN 'KeHE'        THEN rates.rate_kehe
        ELSE rates.rate_regional
    END AS structural_trade_dollars
FROM channel_revenue cr
CROSS JOIN channel_rates rates
ORDER BY cr.revenue DESC;
