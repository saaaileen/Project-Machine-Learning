import argparse
from core.services. import capture

def main():
    parser = argparse.ArgumentParser(description="Test Live Network Capture")
    parser.add_argument("--interface", "-i", type=str, required=True, 
                        help="Network interface to listen to (e.g., eth0, wlan0, lo)")
    parser.add_argument("--duration", "-d", type=int, default=15, 
                        help="Duration to capture in seconds (default: 15)")
    parser.add_argument("--output", "-o", type=str, default="test_live_flows.csv",
                        help="Output CSV file path (default: test_live_flows.csv)")
    args = parser.parse_args()

    print(f"[*] Starting live capture on interface '{args.interface}' for {args.duration} seconds...")
    
    # Call the capture function from feature_extractor.py
    df = capture(source=args.interface, duration_seconds=args.duration, output_csv=args.output)

    if df is not None and not df.empty:
        print("\n" + "="*50)
        print("--- Capture Successful! ---")
        print(f"Shape of the captured dataframe: {df.shape}")
        print("="*50)
        print("\nFirst 10 rows:")
        # Print all columns for the first 10 rows
        import pandas as pd
        pd.set_option('display.max_columns', None)
        print(df.head(10))
    else:
        print("\n[!] No data captured or capture failed. Please check the following:")
        print("    1. Did you specify the correct interface? (use 'ip a' or 'ifconfig' to check)")
        print("    2. Do you have root/sudo permissions? Live capture usually requires sudo.")
        print("    3. Was there any network traffic during the capture window?")

if __name__ == "__main__":
    main()
