CREATE TABLE IF NOT EXISTS hmda_features AS SELECT *, 

loan_amount / TRY_CAST(income AS DOUBLE) AS loan_to_income_ratio,

CASE 
    WHEN action_taken IN(3, 7) THEN 1 
    WHEN action_taken IN (1, 2) THEN 0 
END AS is_denied, 

CASE 
    WHEN TRY_CAST(income AS DOUBLE) < 50 THEN 'Low' 
    WHEN TRY_CAST(income AS DOUBLE) < 100 THEN 'Medium' 
    WHEN TRY_CAST(income AS DOUBLE) < 150 THEN 'High' 
    WHEN TRY_CAST(income AS DOUBLE) < 200 THEN 'Very High' 
    ELSE 'Ultra High' 
END AS income_band, 

CASE 
    WHEN loan_amount < 200 THEN 'Low' 
    WHEN loan_amount < 400 THEN 'Medium' 
    WHEN loan_amount < 700 THEN 'High' 
    ELSE 'Very High' 
END AS loan_amount_band, 

CASE 
    WHEN TRY_CAST(applicant_age AS DOUBLE) < 25 THEN '<25' 
    WHEN TRY_CAST(applicant_age AS DOUBLE) < 32 THEN '25-32' 
    WHEN TRY_CAST(applicant_age AS DOUBLE) < 45 THEN '33-45' 
    WHEN TRY_CAST(applicant_age AS DOUBLE) < 65 THEN '45-65' 
    ELSE '65+' 
END AS applicant_age_band, 

TRY_CAST(debt_to_income_ratio AS DOUBLE) + TRY_CAST(loan_to_value_ratio AS DOUBLE) AS dti_ltv_risk

FROM hmda_clean