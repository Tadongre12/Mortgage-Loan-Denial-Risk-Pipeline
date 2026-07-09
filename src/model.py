import duckdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report, roc_auc_score
from sklearn.preprocessing import StandardScaler




con = duckdb.connect("data/hmda.duckdb")
hmda_df = con.execute("SELECT * FROM hmda_final").df()
con.close()
hmda_df = hmda_df.reset_index(drop=True)


#Replace string placeholders
hmda_df = hmda_df.replace(["NA", "Exempt", ""], pd.NA)

#Map age ranges
age_map = {'<25': 22, '25-34': 29, '35-44': 39, '45-54': 49, '55-64': 59, '65-74': 69, '>74': 77}
hmda_df['applicant_age'] = hmda_df['applicant_age'].map(age_map)

#Convert numeric columns
numeric_cols = ['loan_amount', 'loan_to_value_ratio', 
                'income', 'debt_to_income_ratio', 'property_value',
                'loan_to_income_ratio',
                'avg_unemployment_rate', 'avg_hpi', 'avg_mortgage_rate']
for col in numeric_cols:
    hmda_df[col] = pd.to_numeric(hmda_df[col], errors='coerce')

#Replace infinity with NaN
hmda_df = hmda_df.replace([np.inf, -np.inf], np.nan)

# Drop nulls and filter on hmda_df before splitting
hmda_df = hmda_df.dropna(subset=numeric_cols + ['applicant_age'])
hmda_df = hmda_df[hmda_df['is_denied'].notna()]

#Define X and y
X = hmda_df.drop(columns=["action_taken", "dti_ltv_risk", "derived_race", "derived_sex", "denial_reason-1", "state", "income_band", "loan_amount_band", "applicant_age_band", "is_denied", "derived_ethnicity", "county_code", "interest_rate"])
y = hmda_df["is_denied"]

#Encode categoricals
X = pd.get_dummies(X, columns=["state_code", "loan_type", "loan_purpose", "lien_status"])
print(y.value_counts())
print(X.isnull().sum()[X.isnull().sum() > 0])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

X_test_df = pd.DataFrame(X_test, columns=X.columns)

#Feature scaling
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

#Create the model
model = LogisticRegression(max_iter=1000, class_weight="balanced")
#Train it — learn patterns from training data
model.fit(X_train, y_train)
#Make predictions on test data
y_pred = model.predict(X_test)
#Get probabilities for ROC-AUC
y_prob = model.predict_proba(X_test)[:, 1]
#Evaluate
print(classification_report(y_test, y_pred))
print("ROC-AUC:", roc_auc_score(y_test, y_prob))

# Export feature importance
feature_names = X.columns.tolist()
coefficients = model.coef_[0]
importance_df = pd.DataFrame({
    'feature': feature_names,
    'coefficient': coefficients
})
importance_df = importance_df.reindex(importance_df['coefficient'].abs().sort_values(ascending=False).index)
importance_df.to_csv("data/processed/feature_importance.csv", index=False)
print("Feature importance exported.")

# Export for Tableau
tableau_df = hmda_df.loc[y_test.index].copy()
tableau_df['predicted'] = y_pred
tableau_df['denial_probability'] = y_prob
tableau_df.to_csv("data/processed/hmda_predictions.csv", index=False)