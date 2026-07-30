import pandas as pd
import numpy as np
import os

def extract_features(window_df):
    """
    Extracts summary statistics (features) from a single time window dataframe.
    """
    features = {}
    
    # Compute mean, standard deviation, min, and max for each sensor column
    for col in ["ax", "ay", "az", "gx", "gy", "gz"]:
        features[f"{col}_mean"] = window_df[col].mean()
        features[f"{col}_std"] = window_df[col].std()
        features[f"{col}_min"] = window_df[col].min()
        features[f"{col}_max"] = window_df[col].max()
        
    return features

def main():
    input_path = os.path.join("backend", "driving_data.csv")
    output_path = os.path.join("backend", "features.csv")
    
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found. Please run simulate_data.py first.")
        return
        
    print(f"Loading raw dataset from {input_path}...")
    df = pd.read_csv(input_path)
    
    # Window settings
    sampling_rate_hz = 10
    window_duration_sec = 3
    window_size = sampling_rate_hz * window_duration_sec # 30 samples
    overlap = 15 # 50% overlap (15 samples)
    
    feature_rows = []
    
    print("Processing time-series data into features using sliding windows...")
    
    # Process the dataset in sliding windows
    # Since the raw data is concatenated, we process each continuous label group separately
    # to avoid mixing behaviors at the transition boundaries.
    for label in df["label"].unique():
        sub_df = df[df["label"] == label].reset_index(drop=True)
        n_samples = len(sub_df)
        
        start_idx = 0
        while start_idx + window_size <= n_samples:
            window = sub_df.iloc[start_idx : start_idx + window_size]
            
            # Extract features from this window
            feats = extract_features(window)
            feats["label"] = label
            feature_rows.append(feats)
            
            # Slide window forward
            start_idx += (window_size - overlap)
            
    # Save features to CSV
    features_df = pd.DataFrame(feature_rows)
    features_df.to_csv(output_path, index=False)
    print(f"Feature dataset successfully created and saved to {output_path}")
    print(f"Total feature records: {len(features_df)}")
    print(features_df.head(2))

if __name__ == "__main__":
    main()
