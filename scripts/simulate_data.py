import numpy as np
import pandas as pd
import os

# Create backend directory if it doesn't exist
os.makedirs("backend", exist_ok=True)

# Set random seed for reproducibility
np.random.seed(42)

def generate_segment(label, duration_sec=60, sampling_rate_hz=10):
    """
    Generates a time-series segment of simulated accelerometer (ax, ay, az) 
    and gyroscope (gx, gy, gz) readings representing a driving behavior profile.
    """
    n_samples = duration_sec * sampling_rate_hz
    time = np.linspace(0, duration_sec, n_samples)
    
    # Base acceleration: Gravity is on the Z-axis (around 9.81 m/s^2)
    # Accelerometer readings are in m/s^2, Gyroscope in degrees per second (deg/s)
    ax = np.zeros(n_samples)
    ay = np.zeros(n_samples)
    az = np.ones(n_samples) * 9.81
    
    gx = np.zeros(n_samples)
    gy = np.zeros(n_samples)
    gz = np.zeros(n_samples)
    
    if label == "Safe":
        # Small random vibrations and smooth velocity changes
        ax += np.random.normal(0, 0.5, n_samples)
        ay += np.random.normal(0, 0.5, n_samples)
        az += np.random.normal(0, 0.5, n_samples)
        
        gx += np.random.normal(0, 2.0, n_samples)
        gy += np.random.normal(0, 2.0, n_samples)
        gz += np.random.normal(0, 2.0, n_samples)
        
    elif label == "Moderate Risk":
        # Moderately high values, occasional harder deceleration/turns
        # Base noise is slightly higher
        ax += np.random.normal(0, 1.2, n_samples)
        ay += np.random.normal(0, 1.2, n_samples)
        az += np.random.normal(0, 1.2, n_samples)
        
        gx += np.random.normal(0, 8.0, n_samples)
        gy += np.random.normal(0, 8.0, n_samples)
        gz += np.random.normal(0, 8.0, n_samples)
        
        # Add intermittent braking/turning events
        for _ in range(3):
            idx = np.random.randint(10, n_samples - 10)
            ax[idx-5:idx+5] += np.random.choice([-3.0, 2.5], 10)  # Moderate braking/acceleration
            gz[idx-5:idx+5] += np.random.choice([-15.0, 15.0], 10) # Moderate turn
            
    elif label == "High Risk":
        # Extreme noise, sudden spikes corresponding to sudden braking, swerving, crashing
        ax += np.random.normal(0, 2.5, n_samples)
        ay += np.random.normal(0, 2.5, n_samples)
        az += np.random.normal(0, 2.5, n_samples)
        
        gx += np.random.normal(0, 18.0, n_samples)
        gy += np.random.normal(0, 18.0, n_samples)
        gz += np.random.normal(0, 18.0, n_samples)
        
        # Add severe sudden braking, rapid acceleration and extreme swerving events
        for _ in range(5):
            idx = np.random.randint(10, n_samples - 10)
            # Extreme deceleration (hard brake)
            ax[idx-4:idx+4] += np.random.uniform(-8.0, -6.0, 8) 
            # Extreme side-to-side swerves
            ay[idx-4:idx+4] += np.random.uniform(-7.0, 7.0, 8)
            # High rate of angular rotation
            gz[idx-4:idx+4] += np.random.uniform(-45.0, 45.0, 8)
            gy[idx-4:idx+4] += np.random.uniform(-25.0, 25.0, 8)

    # Compile dataset segment
    df = pd.DataFrame({
        "ax": ax, "ay": ay, "az": az,
        "gx": gx, "gy": gy, "gz": gz,
        "label": label
    })
    return df

def main():
    print("Generating simulated driving data...")
    # Generate 5 minutes of each behavior to create a balanced dataset
    safe_data = generate_segment("Safe", duration_sec=300)
    moderate_data = generate_segment("Moderate Risk", duration_sec=300)
    high_data = generate_segment("High Risk", duration_sec=300)
    
    # Combine the datasets
    dataset = pd.concat([safe_data, moderate_data, high_data], ignore_index=True)
    
    # Save raw data
    output_path = os.path.join("backend", "driving_data.csv")
    dataset.to_csv(output_path, index=False)
    print(f"Dataset successfully created and saved to {output_path}")
    print(f"Total samples: {len(dataset)}")

if __name__ == "__main__":
    main()
