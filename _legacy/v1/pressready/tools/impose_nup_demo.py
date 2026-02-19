"""
N-Up Imposition Demo Script

Demonstrates the impose_nup() function with a sample PDF.

Usage:
    python -m pressready.tools.impose_nup_demo <input.pdf> [output.pdf]

Default output: output_imposed.pdf
Default settings: 2-Up on A3, 5mm margin, 5mm gap

Examples:
    python -m pressready.tools.impose_nup_demo input.pdf
    python -m pressready.tools.impose_nup_demo input.pdf my_output.pdf
"""

import sys
import os

from pressready.engine.impose import impose_nup


def main():
    # Parse arguments
    if len(sys.argv) < 2:
        print(__doc__)
        print("Error: No input file specified.")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "output_imposed.pdf"
    
    # Check input exists
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    # Imposition settings
    sheet_preset = "A3"
    nup = 2
    margin_mm = 5.0
    gap_mm = 5.0
    
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    print(f"Settings: {nup}-Up on {sheet_preset}, margin={margin_mm}mm, gap={gap_mm}mm")
    print()
    
    try:
        num_sheets = impose_nup(
            input_path=input_path,
            output_path=output_path,
            sheet_preset=sheet_preset,
            nup=nup,
            margin_mm=margin_mm,
            gap_mm=gap_mm,
        )
        print(f"Success! Created {num_sheets} output sheet(s).")
        print(f"Output saved to: {output_path}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
