#!/usr/bin/env python3
"""
Trim the first N seconds from an asciinema recording.

Usage:
    python trim_asciinema.py input.cast output.cast [seconds_to_skip]

Example:
    python trim_asciinema.py us-crop-demo.cast us-crop-demo-edited.cast 3
"""

import json
import sys

def trim_cast(input_file, output_file, skip_seconds):
    """
    Remove the first skip_seconds from an asciinema recording.

    Args:
        input_file: Path to input .cast file
        output_file: Path to output .cast file
        skip_seconds: Number of seconds to skip from the beginning
    """
    print(f"📹 Trimming {input_file}...")
    print(f"   Skipping first {skip_seconds} seconds")

    # Read original file
    with open(input_file, 'r') as f:
        lines = f.readlines()

    # Parse header (line 1) - JSON metadata
    header = json.loads(lines[0])

    # Parse events (lines 2+) - [timestamp, event_type, data]
    # Note: timestamps are RELATIVE (time since last event)
    events = [json.loads(line) for line in lines[1:]]

    print(f"   Total events: {len(events)}")

    # Calculate cumulative time to find total duration
    cumulative_time = 0
    for event in events:
        cumulative_time += event[0]
    print(f"   Duration: {cumulative_time:.1f} seconds")

    # Find the index where we've accumulated skip_seconds
    cumulative = 0
    skip_index = 0
    for i, event in enumerate(events):
        cumulative += event[0]
        if cumulative >= skip_seconds:
            skip_index = i + 1  # Start from next event
            break

    print(f"   Skipping {skip_index} events ({cumulative:.1f} seconds)")

    # Get events after skip point
    filtered = events[skip_index:]
    print(f"   Events after trim: {len(filtered)}")

    # No timestamp adjustment needed - they're already relative!
    adjusted = filtered

    # Calculate new total duration
    new_duration = sum(e[0] for e in adjusted) if adjusted else 0
    print(f"   New duration: {new_duration:.1f} seconds")

    # Write to output file
    with open(output_file, 'w') as f:
        # Write header
        f.write(json.dumps(header) + '\n')

        # Write adjusted events
        for event in adjusted:
            f.write(json.dumps(event) + '\n')

    print(f"✅ Saved to {output_file}")
    print(f"\nPreview with: asciinema play {output_file}")
    print(f"Upload with:  asciinema upload {output_file}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python trim_asciinema.py input.cast output.cast [seconds_to_skip]")
        print("\nExample:")
        print("  python trim_asciinema.py us-crop-demo.cast us-crop-demo-edited.cast 3")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    skip_seconds = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0

    try:
        trim_cast(input_file, output_file, skip_seconds)
    except FileNotFoundError:
        print(f"❌ Error: File '{input_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
