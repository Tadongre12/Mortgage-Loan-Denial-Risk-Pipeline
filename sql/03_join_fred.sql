CREATE TABLE IF NOT EXISTS hmda_final AS
SELECT *
FROM hmda_features
JOIN (SELECT 
    unemp.state,
    unemp.avg_unemployment_rate,
    hpi.avg_hpi,
    (SELECT AVG(mortgage_rate_30yr) FROM mortgage_rate) AS avg_mortgage_rate
FROM (
    SELECT state, AVG(unemployment_rate) AS avg_unemployment_rate
    FROM (
        SELECT state, unemployment_rate FROM NC_unemployment_rate
        UNION ALL
        SELECT state, unemployment_rate FROM VA_unemployment_rate
    )
    GROUP BY state
) AS unemp
JOIN (
    SELECT state, AVG(housing_price_index) AS avg_hpi
    FROM (
        SELECT state, housing_price_index FROM NC_housing_price_index
        UNION ALL
        SELECT state, housing_price_index FROM VA_housing_price_index
    )
    GROUP BY state
) AS hpi ON unemp.state = hpi.state) AS macro ON hmda_features.state_code = macro.state