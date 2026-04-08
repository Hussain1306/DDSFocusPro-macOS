import os
import json
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report


# Mapping: Table  Target Column
TARGETS = {
    "leads": "converted",
    "proposal": "status",
    "project": "completed",
    "accounting": "paid",
    "employee": "active",  # Change to 'performance_score' if regression needed
}


def train_model_for_table(veritabani, table_name, target_column, limit=1000):
    print(f"\n Training model for `{table_name}` to predict `{target_column}`")

    # Fetch data
    query = f"SELECT * FROM {table_name} LIMIT {limit}"
    records = veritabani.sorgu_calistir(query)

    if not records:
        print(f" No data retrieved from `{table_name}`.")
        return None

    df = pd.DataFrame(records)

    if target_column not in df.columns:
        print(f" Target column `{target_column}` not found in `{table_name}`.")
        return None

    df = df.dropna(subset=[target_column])

    # Drop ID column if present
    if "id" in df.columns:
        df.drop(columns=["id"], inplace=True)

    X = df.drop(columns=[target_column])
    y = df[target_column]

    # Encode categorical features
    X = pd.get_dummies(X)

    # Encode label if it's not numeric
    if y.dtype == "object":
        y = pd.factorize(y)[0]

    # Train/Test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Train model
    model = RandomForestClassifier()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    # Generate evaluation report
    report = classification_report(y_test, y_pred, output_dict=True)
    print(f" Model trained for `{table_name}`. Accuracy: {report['accuracy']:.2f}")

    return {
        "table": table_name,
        "target": target_column,
        "accuracy": report["accuracy"],
        "metrics": report,
    }


def train_models_for_all_tables(veritabani):
    os.makedirs("logs", exist_ok=True)
    all_results = []

    for table_name, target_column in TARGETS.items():
        result = train_model_for_table(veritabani, table_name, target_column)
        if result:
            all_results.append(result)

    # Save report
    with open("logs/ml_report.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print("\n All results saved to: logs/ml_report.json")

