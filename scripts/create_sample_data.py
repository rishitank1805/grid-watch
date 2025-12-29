"""
Generate sample smart meter data for testing.
"""
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


def generate_sample_data(output_file: str, num_meters: int = 10, days: int = 7, interval_minutes: int = 30):
    """
    Generate sample smart meter data.
    
    Args:
        output_file: Output CSV file path
        num_meters: Number of meters to generate
        days: Number of days of data
        interval_minutes: Interval between readings in minutes
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    start_time = datetime.now() - timedelta(days=days)
    interval = timedelta(minutes=interval_minutes)
    
    total_readings = int((days * 24 * 60) / interval_minutes)
    
    print(f"Generating {total_readings} readings for {num_meters} meters...")
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['meter_id', 'timestamp', 'consumption_kwh'])
        writer.writeheader()
        
        for meter_id in range(1, num_meters + 1):
            meter_id_str = f"METER_{meter_id:04d}"
            current_time = start_time
            
            # Base consumption varies by meter
            base_consumption = random.uniform(0.5, 5.0)
            
            for _ in range(total_readings):
                # Add some variation to consumption
                consumption = base_consumption + random.uniform(-0.3, 0.3)
                consumption = max(0.0, consumption)  # Ensure non-negative
                
                writer.writerow({
                    'meter_id': meter_id_str,
                    'timestamp': current_time.isoformat(),
                    'consumption_kwh': round(consumption, 3)
                })
                
                current_time += interval
    
    print(f"Generated sample data: {output_path}")
    print(f"  Meters: {num_meters}")
    print(f"  Days: {days}")
    print(f"  Total readings: {num_meters * total_readings}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate sample smart meter data')
    parser.add_argument('--output', default='data/sample_data.csv', help='Output file path')
    parser.add_argument('--meters', type=int, default=10, help='Number of meters')
    parser.add_argument('--days', type=int, default=7, help='Number of days of data')
    parser.add_argument('--interval', type=int, default=30, help='Interval in minutes')
    
    args = parser.parse_args()
    
    generate_sample_data(args.output, args.meters, args.days, args.interval)

