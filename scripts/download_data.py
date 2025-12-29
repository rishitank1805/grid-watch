"""
Script to download and prepare smart meter datasets.
"""
import csv
import os
import sys
from pathlib import Path
from datetime import datetime
import argparse


def download_goiener_sample(output_file: str):
    """
    Download GoiEner sample dataset from Zenodo.
    
    Note: This is a sample. Full dataset available at:
    https://zenodo.org/records/14949245
    """
    import urllib.request
    
    url = "https://zenodo.org/records/14949245/files/goiener_sample.csv?download=1"
    
    print(f"Downloading GoiEner sample dataset from {url}...")
    try:
        urllib.request.urlretrieve(url, output_file)
        print(f"Downloaded to {output_file}")
        return True
    except Exception as e:
        print(f"Error downloading: {e}")
        return False


def convert_goiener_to_standard(input_file: str, output_file: str):
    """
    Convert GoiEner dataset format to our standard format.
    
    GoiEner format may vary, this is a template converter.
    """
    print(f"Converting {input_file} to standard format...")
    
    # Read input and check format
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        if not rows:
            print("No data found in input file")
            return False
        
        # Check what columns we have
        sample_row = rows[0]
        print(f"Input columns: {list(sample_row.keys())}")
        
        # Try to map to our format
        # This is a template - adjust based on actual GoiEner format
        with open(output_file, 'w', newline='', encoding='utf-8') as out:
            writer = csv.DictWriter(out, fieldnames=['meter_id', 'timestamp', 'consumption_kwh'])
            writer.writeheader()
            
            for row in rows:
                # Adjust these mappings based on actual GoiEner format
                meter_id = row.get('meter_id') or row.get('id') or row.get('meterId') or 'UNKNOWN'
                timestamp = row.get('timestamp') or row.get('time') or row.get('datetime')
                consumption = row.get('consumption_kwh') or row.get('consumption') or row.get('kwh') or row.get('value')
                
                if meter_id and timestamp and consumption:
                    try:
                        # Ensure timestamp is in ISO format
                        if not timestamp.endswith('Z') and 'T' in timestamp:
                            # Already ISO-like
                            pass
                        elif ' ' in timestamp:
                            # Convert space-separated to ISO
                            timestamp = timestamp.replace(' ', 'T')
                        
                        writer.writerow({
                            'meter_id': str(meter_id),
                            'timestamp': timestamp,
                            'consumption_kwh': float(consumption)
                        })
                    except (ValueError, TypeError) as e:
                        print(f"Skipping row due to error: {e}")
                        continue
        
        print(f"Converted {len(rows)} rows to {output_file}")
        return True


def main():
    parser = argparse.ArgumentParser(description='Download and prepare smart meter datasets')
    parser.add_argument('--dataset', choices=['goiener', 'sample'], default='sample',
                       help='Dataset to download (default: sample)')
    parser.add_argument('--output', default='data/sample_data.csv',
                       help='Output file path (default: data/sample_data.csv)')
    parser.add_argument('--convert', action='store_true',
                       help='Convert downloaded dataset to standard format')
    
    args = parser.parse_args()
    
    # Create data directory if it doesn't exist
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if args.dataset == 'goiener':
        temp_file = output_path.parent / 'goiener_raw.csv'
        if download_goiener_sample(str(temp_file)):
            if args.convert:
                convert_goiener_to_standard(str(temp_file), args.output)
            else:
                # Just copy if no conversion needed
                import shutil
                shutil.copy(temp_file, args.output)
                print(f"Data saved to {args.output}")
    elif args.dataset == 'sample':
        # Generate sample data instead
        from scripts.create_sample_data import generate_sample_data
        generate_sample_data(args.output, num_meters=20, days=30, interval_minutes=30)
        print(f"Sample data generated: {args.output}")


if __name__ == "__main__":
    main()

