"""
Generate Sample PDF for Testing

Creates a multi-page sample PDF with numbered pages.
Useful for testing imposition without needing external PDFs.

Usage:
    python -m pressready.tools.generate_sample_pdf [output.pdf] [num_pages]

Default: sample_8pages.pdf with 8 pages
"""

import sys
import fitz  # PyMuPDF

from pressready.engine.utils import mm_to_pt


def generate_sample_pdf(output_path: str, num_pages: int = 8) -> None:
    """
    Generate a sample PDF with numbered pages.
    
    Args:
        output_path: Output file path
        num_pages: Number of pages to generate
    """
    # A4 size in points
    width = mm_to_pt(210)
    height = mm_to_pt(297)
    
    doc = fitz.open()
    
    colors = [
        (0.95, 0.95, 1.0),   # Light blue
        (1.0, 0.95, 0.95),   # Light red
        (0.95, 1.0, 0.95),   # Light green
        (1.0, 1.0, 0.9),     # Light yellow
        (0.95, 0.9, 1.0),    # Light purple
        (1.0, 0.95, 0.9),    # Light orange
        (0.9, 1.0, 1.0),     # Light cyan
        (1.0, 0.9, 0.95),    # Light pink
    ]
    
    for i in range(num_pages):
        page = doc.new_page(width=width, height=height)
        
        # Background color
        bg_color = colors[i % len(colors)]
        bg_rect = fitz.Rect(0, 0, width, height)
        page.draw_rect(bg_rect, color=None, fill=bg_color)
        
        # Border
        border_rect = fitz.Rect(20, 20, width - 20, height - 20)
        page.draw_rect(border_rect, color=(0.5, 0.5, 0.5), width=2)
        
        # Page number (large, centered)
        page_num = str(i + 1)
        fontsize = 120
        text_width = fitz.get_text_length(page_num, fontname="helv", fontsize=fontsize)
        x = (width - text_width) / 2
        y = height / 2 + fontsize / 3
        
        page.insert_text(
            (x, y),
            page_num,
            fontname="helv",
            fontsize=fontsize,
            color=(0.3, 0.3, 0.3),
        )
        
        # Label
        label = f"Page {i + 1} of {num_pages}"
        label_fontsize = 14
        label_width = fitz.get_text_length(label, fontname="helv", fontsize=label_fontsize)
        page.insert_text(
            ((width - label_width) / 2, height - 50),
            label,
            fontname="helv",
            fontsize=label_fontsize,
            color=(0.5, 0.5, 0.5),
        )
        
        # Corner markers
        marker_size = 30
        corners = [
            (30, 40),
            (width - 30 - marker_size, 40),
            (30, height - 40),
            (width - 30 - marker_size, height - 40),
        ]
        for cx, cy in corners:
            page.draw_line((cx, cy), (cx + marker_size, cy), color=(0, 0, 0), width=0.5)
            page.draw_line((cx, cy), (cx, cy + marker_size * (1 if cy < height/2 else -1)), 
                          color=(0, 0, 0), width=0.5)
    
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    
    print(f"Generated {num_pages}-page sample PDF: {output_path}")


def main():
    output_path = sys.argv[1] if len(sys.argv) > 1 else "sample_8pages.pdf"
    num_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    
    generate_sample_pdf(output_path, num_pages)


if __name__ == "__main__":
    main()
