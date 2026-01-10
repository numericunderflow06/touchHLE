#!/usr/bin/env python3
"""Analyze a frame capture for black pixels and determine pass/fail verdict."""

import sys
import argparse
from datetime import datetime
from pathlib import Path
from PIL import Image

def analyze_black_pixels(image_path, black_threshold=10):
    """
    Analyze an image for black pixels.

    Args:
        image_path: Path to the image file
        black_threshold: RGB values below this are considered "black" (default 10)

    Returns:
        dict with analysis results
    """
    img = Image.open(image_path)
    pixels = img.load()
    width, height = img.size

    total_pixels = width * height
    black_pixels = 0

    for y in range(height):
        for x in range(width):
            pixel = pixels[x, y]
            # Handle both RGB and RGBA
            r, g, b = pixel[:3]
            if r <= black_threshold and g <= black_threshold and b <= black_threshold:
                black_pixels += 1

    proportion = black_pixels / total_pixels

    return {
        'width': width,
        'height': height,
        'total_pixels': total_pixels,
        'black_pixels': black_pixels,
        'proportion': proportion,
        'percentage': proportion * 100
    }

def check_black_pixel_threshold(image_path, max_black_percent=15.0, black_threshold=10):
    """
    Check if black pixels are below the threshold percentage.

    Args:
        image_path: Path to the image file
        max_black_percent: Maximum allowed percentage of black pixels (default 15%)
        black_threshold: RGB values below this are considered "black" (default 10)

    Returns:
        tuple: (passed: bool, results: dict)
    """
    results = analyze_black_pixels(image_path, black_threshold)
    passed = results['percentage'] < max_black_percent
    results['max_black_percent'] = max_black_percent
    results['passed'] = passed
    results['verdict'] = 'PASS' if passed else 'FAIL'
    return passed, results

def write_results_to_file(results, output_path, image_path):
    """Write analysis results to a text file."""
    with open(output_path, 'w') as f:
        f.write("=" * 50 + "\n")
        f.write("BLACK PIXEL ANALYSIS REPORT\n")
        f.write("=" * 50 + "\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Image: {image_path}\n")
        f.write("-" * 50 + "\n")
        f.write(f"Image size: {results['width']} x {results['height']}\n")
        f.write(f"Total pixels: {results['total_pixels']:,}\n")
        f.write(f"Black pixels: {results['black_pixels']:,}\n")
        f.write(f"Black pixel percentage: {results['percentage']:.2f}%\n")
        f.write(f"Threshold: < {results['max_black_percent']:.1f}%\n")
        f.write("-" * 50 + "\n")
        f.write(f"VERDICT: {results['verdict']}\n")
        if results['passed']:
            f.write(f"  Black pixels ({results['percentage']:.2f}%) are below {results['max_black_percent']:.1f}% threshold.\n")
        else:
            f.write(f"  Black pixels ({results['percentage']:.2f}%) exceed {results['max_black_percent']:.1f}% threshold.\n")
        f.write("=" * 50 + "\n")

def main():
    parser = argparse.ArgumentParser(description='Analyze frame capture for black pixels')
    parser.add_argument('image', nargs='?', default='captures/debug_frame.png',
                        help='Path to image file (PNG or PPM)')
    parser.add_argument('--threshold', '-t', type=float, default=15.0,
                        help='Maximum allowed black pixel percentage (default: 15.0)')
    parser.add_argument('--black-threshold', '-b', type=int, default=10,
                        help='RGB threshold below which pixels are considered black (default: 10)')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Output file path for results (default: print to stdout only)')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Only print verdict line')
    args = parser.parse_args()

    image_path = args.image

    passed, results = check_black_pixel_threshold(
        image_path,
        max_black_percent=args.threshold,
        black_threshold=args.black_threshold
    )

    if not args.quiet:
        print(f"Analyzing: {image_path}")
        print("-" * 40)
        print(f"Image size: {results['width']} x {results['height']}")
        print(f"Total pixels: {results['total_pixels']:,}")
        print(f"Black pixels: {results['black_pixels']:,}")
        print(f"Percentage: {results['percentage']:.2f}%")
        print(f"Threshold: < {args.threshold:.1f}%")
        print("-" * 40)

    print(f"VERDICT: {results['verdict']} ({results['percentage']:.2f}% black pixels)")

    if args.output:
        write_results_to_file(results, args.output, image_path)
        if not args.quiet:
            print(f"Results written to: {args.output}")

    # Exit with code 0 if passed, 1 if failed
    sys.exit(0 if passed else 1)

if __name__ == '__main__':
    main()
