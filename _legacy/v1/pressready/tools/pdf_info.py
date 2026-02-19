"""
PDF Info Tool - Sanity check script for loading PDFs.

Usage:
    python -m pressready.tools.pdf_info <path_to_pdf>

Prints:
    - Page count
    - Page sizes (width x height in points and mm)
    - Basic document metadata
"""

import sys
import fitz  # PyMuPDF

from pressready.engine.utils import pt_to_mm


def print_pdf_info(path: str) -> None:
    """Load a PDF and print its basic info."""
    try:
        doc = fitz.open(path)
    except Exception as e:
        print(f"Error opening PDF: {e}")
        sys.exit(1)
    
    print(f"File: {path}")
    print(f"Page count: {len(doc)}")
    print()
    
    # Print page sizes
    print("Page sizes:")
    unique_sizes = {}
    for i, page in enumerate(doc):
        rect = page.rect
        w_pt, h_pt = rect.width, rect.height
        w_mm, h_mm = pt_to_mm(w_pt), pt_to_mm(h_pt)
        size_key = (round(w_pt, 1), round(h_pt, 1))
        
        if size_key not in unique_sizes:
            unique_sizes[size_key] = []
        unique_sizes[size_key].append(i + 1)
    
    for (w_pt, h_pt), pages in unique_sizes.items():
        w_mm, h_mm = pt_to_mm(w_pt), pt_to_mm(h_pt)
        page_list = pages[:5]
        more = f"... (+{len(pages)-5} more)" if len(pages) > 5 else ""
        print(f"  {w_pt:.1f} x {h_pt:.1f} pt ({w_mm:.1f} x {h_mm:.1f} mm)")
        print(f"    Pages: {page_list}{more}")
    
    print()
    
    # Print metadata
    meta = doc.metadata
    if meta:
        print("Metadata:")
        for key, value in meta.items():
            if value:
                print(f"  {key}: {value}")
    
    doc.close()
    print("\nPDF loaded successfully.")


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m pressready.tools.pdf_info <path_to_pdf>")
        sys.exit(1)
    
    print_pdf_info(sys.argv[1])


if __name__ == "__main__":
    main()
