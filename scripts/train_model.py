import pandas as pd
import numpy as np
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

def main():
    features_path = os.path.join("backend", "features.csv")
    model_path = os.path.join("backend", "steersafe_model.pkl")
    
    if not os.path.exists(features_path):
        print(f"Error: {features_path} not found. Please run prepare_features.py first.")
        return
        
    print(f"Loading feature dataset from {features_path}...")
    df = pd.read_csv(features_path)
    
    # Split into features (X) and labels (y)
    X = df.drop(columns=["label"])
    y = df["label"]
    
    # Split into training and testing sets (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print(f"Training set size: {X_train.shape[0]} samples")
    print(f"Testing set size: {X_test.shape[0]} samples")
    
    # Initialize Random Forest Classifier
    # We set reasonable constraints (n_estimators=20, max_depth=5) to keep the model lightweight ("TinyML" style)
    print("Training lightweight Random Forest model...")
    model = RandomForestClassifier(n_estimators=20, max_depth=5, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate model
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print("\n=== Model Evaluation ===")
    print(f"Accuracy: {accuracy * 100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Save the trained model to a file using pickle
    print(f"Saving model to {model_path}...")
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
        
    # Also save the list of feature column names for predictions later
    feature_columns_path = os.path.join("backend", "feature_columns.pkl")
    with open(feature_columns_path, "wb") as f:
        pickle.dump(list(X.columns), f)
        
    print("Training and serialization completed successfully!")

if __name__ == "__main__":
    main()
