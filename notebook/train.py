import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

def main():
    # 1. Load the dataset using dynamic path resolution
    # (handles running the script from either the root or the notebook directory)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "notebook" in os.path.abspath(__file__) else os.path.abspath(".")
    csv_path = os.path.join(base_dir, "loan_approval_dataset.csv")

    print(f"Loading dataset from: {csv_path}")
    if not os.path.exists(csv_path):
        print(f"Error: Dataset not found at {csv_path}")
        return

    df = pd.read_csv(csv_path)

    # 2. Clean column names (remove leading/trailing spaces)
    df.columns = df.columns.str.strip()

    # 3. Clean string values in categorical columns (strip spaces)
    categorical_cols = df.select_dtypes(include=["object"]).columns
    for col in categorical_cols:
        df[col] = df[col].str.strip()

    # 4. Drop loan_id as it is not a feature
    df = df.drop(columns=["loan_id"])

    # 5. Define features and target (Map Target: Approved -> 1, Rejected -> 0)
    X = df.drop(columns=["loan_status"])
    y = df["loan_status"].map({"Approved": 1, "Rejected": 0})

    # 6. Preprocessing setup
    numeric_features = [
        "no_of_dependents", "income_annum", "loan_amount", "loan_term", "cibil_score", 
        "residential_assets_value", "commercial_assets_value", "luxury_assets_value", "bank_asset_value"
    ]
    categorical_features = ["education", "self_employed"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(drop="first"), categorical_features)
        ]
    )

    # 7. Create pipeline with Random Forest Classifier
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced"))
    ])

    # 8. Train-Test Split (stratified on loan_status)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # 9. Train the model
    print("Training the Random Forest model...")
    pipeline.fit(X_train, y_train)

    # 10. Evaluate the model
    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {accuracy:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    # 11. Save the model to the model directory
    model_dir = os.path.join(base_dir, "model")
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "loan_model.pkl")
    joblib.dump(pipeline, model_path)
    print(f"Successfully saved trained model pipeline to {model_path}")

if __name__ == "__main__":
    main()
