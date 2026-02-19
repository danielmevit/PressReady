"""
Imposition engine - N-Up and Booklet layout generation.

Uses PyMuPDF's show_pdf_page for vector-quality placement.
"""

import fitz  # PyMuPDF
from typing import List, Optional, Tuple

from pressready.engine.utils import mm_to_pt, parse_page_range

# Crop mark settings
CROP_MARK_LENGTH_MM = 5.0  # Length of crop mark lines
CROP_MARK_OFFSET_MM = 3.0  # Offset from page edge
CROP_MARK_WIDTH = 0.5      # Line width in points

# Registration mark settings
REG_MARK_SIZE_MM = 5.0     # Size of registration mark
REG_MARK_WIDTH = 0.3       # Line width in points

# Page label settings
LABEL_FONT_SIZE = 8        # Font size in points
LABEL_MARGIN_MM = 5.0      # Distance from sheet edge

# Booklet page ordering for saddle-stitch
# When folded, pages read in correct order


# Sheet size presets in millimeters (width, height) - portrait orientation
SHEET_PRESETS_MM = {
    "A4": (210.0, 297.0),
    "A3": (297.0, 420.0),
    "Letter": (215.9, 279.4),
    "Tabloid": (279.4, 431.8),
}


def draw_registration_mark(page, x: float, y: float, size_mm: float = REG_MARK_SIZE_MM) -> None:
    """
    Draw a registration mark (crosshair with circle) at the given position.
    
    Args:
        page: PyMuPDF page to draw on
        x, y: Center position in points
        size_mm: Size of the mark in mm
    """
    size = mm_to_pt(size_mm)
    half = size / 2
    
    # Draw crosshair
    page.draw_line((x - half, y), (x + half, y), color=(0, 0, 0), width=REG_MARK_WIDTH)
    page.draw_line((x, y - half), (x, y + half), color=(0, 0, 0), width=REG_MARK_WIDTH)
    
    # Draw circle
    radius = size / 4
    page.draw_circle((x, y), radius, color=(0, 0, 0), width=REG_MARK_WIDTH)


def draw_page_labels(page, sheet_w: float, sheet_h: float, 
                     content_margin_pt: float,
                     sheet_num: int, total_sheets: int,
                     filename: str = "", layout_info: str = "") -> None:
    """
    Draw page labels/slugs OUTSIDE the content area, in the slug zone.
    
    Labels are placed in the bottom margin, between content edge and sheet edge.
    
    Args:
        page: PyMuPDF page to draw on
        sheet_w, sheet_h: Sheet dimensions in points
        content_margin_pt: Content margin in points (defines where content ends)
        sheet_num: Current sheet number (1-based)
        total_sheets: Total number of sheets
        filename: Source filename to display
        layout_info: Layout description (e.g., "2-Up on A3")
    """
    # Position labels in the bottom margin (between content and sheet edge)
    # Place text at 60% down in the margin area
    content_bottom = sheet_h - content_margin_pt
    margin_height = content_margin_pt
    
    if margin_height < mm_to_pt(8):  # Need at least 8mm for readable labels
        return  # Skip labels if margin too small
    
    label_y = content_bottom + margin_height * 0.6
    
    # Inset labels 10% from sheet edges to avoid overlap with crop marks at corners
    text_inset = sheet_w * 0.10
    
    # Bottom left: filename and layout (10% from left edge)
    left_text = f"{filename}" if filename else ""
    if layout_info:
        left_text += f"  |  {layout_info}" if left_text else layout_info
    
    if left_text:
        page.insert_text(
            (text_inset, label_y),
            left_text,
            fontsize=LABEL_FONT_SIZE,
            color=(0.4, 0.4, 0.4),
        )
    
    # Bottom right: sheet number (10% from right edge)
    sheet_text = f"Sheet {sheet_num} of {total_sheets}"
    text_width = fitz.get_text_length(sheet_text, fontsize=LABEL_FONT_SIZE)
    page.insert_text(
        (sheet_w - text_inset - text_width, label_y),
        sheet_text,
        fontsize=LABEL_FONT_SIZE,
        color=(0.4, 0.4, 0.4),
    )


def draw_registration_marks_on_sheet(page, sheet_w: float, sheet_h: float, 
                                      content_margin_pt: float) -> None:
    """
    Draw registration marks OUTSIDE the content area, in the margin zone.
    
    Marks are placed between the content edge and sheet edge, centered in the margin.
    Standard positions: 4 corners + 4 edge centers (8 marks total).
    
    Args:
        page: PyMuPDF page to draw on
        sheet_w, sheet_h: Sheet dimensions in points
        content_margin_pt: Content margin in points (defines content boundary)
    """
    if content_margin_pt < mm_to_pt(10):  # Need at least 10mm margin for marks
        return  # Skip marks if margin too small
    
    # Position marks at center of margin zone (between content edge and sheet edge)
    mark_offset = content_margin_pt / 2
    
    # Content boundaries
    content_left = content_margin_pt
    content_right = sheet_w - content_margin_pt
    content_top = content_margin_pt
    content_bottom = sheet_h - content_margin_pt
    
    # Positions: corners and edge centers, all in the margin zone
    positions = [
        # Corners - diagonal from content corners
        (mark_offset, mark_offset),                          # Top-left
        (sheet_w - mark_offset, mark_offset),                # Top-right
        (mark_offset, sheet_h - mark_offset),                # Bottom-left
        (sheet_w - mark_offset, sheet_h - mark_offset),      # Bottom-right
        # Edge centers
        ((content_left + content_right) / 2, mark_offset),   # Top-center
        ((content_left + content_right) / 2, sheet_h - mark_offset),  # Bottom-center
        (mark_offset, (content_top + content_bottom) / 2),   # Left-center
        (sheet_w - mark_offset, (content_top + content_bottom) / 2),  # Right-center
    ]
    
    for x, y in positions:
        draw_registration_mark(page, x, y)


def draw_crop_marks(page, rect: fitz.Rect, 
                    mark_length_mm: float = CROP_MARK_LENGTH_MM,
                    offset_mm: float = CROP_MARK_OFFSET_MM) -> None:
    """
    Draw crop marks around a rectangle.
    
    Args:
        page: PyMuPDF page to draw on
        rect: Rectangle to draw marks around
        mark_length_mm: Length of crop mark lines in mm
        offset_mm: Offset from rectangle edge in mm
    """
    mark_len = mm_to_pt(mark_length_mm)
    offset = mm_to_pt(offset_mm)
    
    x0, y0, x1, y1 = rect.x0, rect.y0, rect.x1, rect.y1
    
    # Corner positions
    corners = [
        # Top-left
        ((x0 - offset - mark_len, y0), (x0 - offset, y0)),  # Horizontal
        ((x0, y0 - offset - mark_len), (x0, y0 - offset)),  # Vertical
        # Top-right
        ((x1 + offset, y0), (x1 + offset + mark_len, y0)),  # Horizontal
        ((x1, y0 - offset - mark_len), (x1, y0 - offset)),  # Vertical
        # Bottom-left
        ((x0 - offset - mark_len, y1), (x0 - offset, y1)),  # Horizontal
        ((x0, y1 + offset), (x0, y1 + offset + mark_len)),  # Vertical
        # Bottom-right
        ((x1 + offset, y1), (x1 + offset + mark_len, y1)),  # Horizontal
        ((x1, y1 + offset), (x1, y1 + offset + mark_len)),  # Vertical
    ]
    
    for start, end in corners:
        page.draw_line(start, end, color=(0, 0, 0), width=CROP_MARK_WIDTH)


def get_sheet_size_pt(preset: str, orientation: str = "landscape") -> Tuple[float, float]:
    """
    Get sheet size in points for a given preset and orientation.
    
    Args:
        preset: Sheet size name (e.g., "A3", "A4")
        orientation: "landscape" or "portrait"
        
    Returns:
        Tuple of (width, height) in points
        
    Raises:
        ValueError: If preset is not recognized
    """
    if preset not in SHEET_PRESETS_MM:
        available = ", ".join(SHEET_PRESETS_MM.keys())
        raise ValueError(f"Unknown sheet preset: '{preset}'. Available: {available}")
    
    w_mm, h_mm = SHEET_PRESETS_MM[preset]
    w_pt, h_pt = mm_to_pt(w_mm), mm_to_pt(h_mm)
    
    # Presets are stored as portrait (width < height)
    # Swap for landscape orientation
    if orientation == "landscape":
        return max(w_pt, h_pt), min(w_pt, h_pt)
    else:  # portrait
        return min(w_pt, h_pt), max(w_pt, h_pt)


def impose_nup(
    input_path: str,
    output_path: str,
    sheet_preset: str = "A3",
    nup: int = 2,
    page_range_expr: Optional[str] = None,
    margin_mm: float = 0.0,
    gap_mm: float = 0.0,
    orientation: str = "landscape",
    crop_marks: bool = False,
    registration_marks: bool = False,
    page_labels: bool = False,
    custom_size_mm: Optional[Tuple[float, float]] = None,
    progress_callback: Optional[callable] = None,
) -> int:
    """
    Create N-Up imposed PDF using vector placement.
    
    Places multiple source pages onto each output sheet in a grid layout.
    Uses show_pdf_page for vector-quality output (no rasterization).
    
    Args:
        input_path: Path to input PDF file
        output_path: Path for output imposed PDF
        sheet_preset: Output sheet size ("A3", "A4", "Letter", "Tabloid")
        nup: Number of pages per sheet (2 or 4)
        page_range_expr: Page range expression (1-based, e.g., "1-4,7,10-12")
                        If None, all pages are used
        margin_mm: Margin around sheet edge in millimeters
        gap_mm: Gap between cells in millimeters
        orientation: Sheet orientation ("landscape" or "portrait")
        crop_marks: Whether to draw crop marks around each page
        registration_marks: Whether to draw registration marks on sheet
        page_labels: Whether to draw page labels in margins
        custom_size_mm: Custom sheet size (width, height) in mm, overrides preset
        progress_callback: Optional callback(current, total) for progress updates
        
    Returns:
        Number of output sheets created
        
    Raises:
        ValueError: If parameters are invalid
        FileNotFoundError: If input file doesn't exist
    """
    # Validate nup
    if nup not in (2, 4):
        raise ValueError(f"nup must be 2 or 4, got {nup}")
    
    # Grid configuration
    if nup == 2:
        cols, rows = 2, 1  # 2 columns, 1 row
    else:  # nup == 4
        cols, rows = 2, 2  # 2 columns, 2 rows
    
    # Get sheet dimensions in points
    if custom_size_mm:
        w_pt = mm_to_pt(custom_size_mm[0])
        h_pt = mm_to_pt(custom_size_mm[1])
        # Apply orientation
        if orientation == "landscape":
            sheet_w, sheet_h = max(w_pt, h_pt), min(w_pt, h_pt)
        else:
            sheet_w, sheet_h = min(w_pt, h_pt), max(w_pt, h_pt)
    else:
        sheet_w, sheet_h = get_sheet_size_pt(sheet_preset, orientation)
    
    # Convert margins and gaps to points
    margin_pt = mm_to_pt(margin_mm)
    gap_pt = mm_to_pt(gap_mm)
    
    # Calculate cell dimensions
    # Available width = sheet_w - 2*margin - (cols-1)*gap
    available_w = sheet_w - 2 * margin_pt - (cols - 1) * gap_pt
    available_h = sheet_h - 2 * margin_pt - (rows - 1) * gap_pt
    
    cell_w = available_w / cols
    cell_h = available_h / rows
    
    if cell_w <= 0 or cell_h <= 0:
        raise ValueError(
            f"Margins and gaps too large for sheet size. "
            f"Cell size would be {cell_w:.1f}x{cell_h:.1f} points"
        )
    
    # Open input document
    src_doc = fitz.open(input_path)
    total_pages = len(src_doc)
    
    if total_pages == 0:
        src_doc.close()
        raise ValueError("Input PDF has no pages")
    
    # Determine which pages to include
    if page_range_expr is None:
        # Use all pages
        page_indices = list(range(total_pages))
    else:
        page_indices = parse_page_range(page_range_expr, total_pages)
    
    num_source_pages = len(page_indices)
    
    # Calculate number of output sheets needed
    num_sheets = (num_source_pages + nup - 1) // nup  # Ceiling division
    
    # Create output document
    out_doc = fitz.open()
    
    # Process each output sheet
    for sheet_idx in range(num_sheets):
        # Report progress
        if progress_callback:
            progress_callback(sheet_idx, num_sheets)
        
        # Create new page with sheet dimensions
        out_page = out_doc.new_page(width=sheet_w, height=sheet_h)
        
        # Place up to nup source pages on this sheet
        for cell_idx in range(nup):
            src_list_idx = sheet_idx * nup + cell_idx
            
            if src_list_idx >= num_source_pages:
                # No more source pages - leave cell blank
                break
            
            src_page_idx = page_indices[src_list_idx]
            
            # Calculate cell position (left-to-right, top-to-bottom)
            col = cell_idx % cols
            row = cell_idx // cols
            
            # Cell rectangle
            x0 = margin_pt + col * (cell_w + gap_pt)
            y0 = margin_pt + row * (cell_h + gap_pt)
            x1 = x0 + cell_w
            y1 = y0 + cell_h
            
            cell_rect = fitz.Rect(x0, y0, x1, y1)
            
            # Place source page into cell (vector placement)
            out_page.show_pdf_page(
                cell_rect,
                src_doc,
                src_page_idx,
                keep_proportion=True,
                overlay=True,
            )
            
            # Draw crop marks if enabled
            if crop_marks:
                draw_crop_marks(out_page, cell_rect)
        
        # Draw registration marks if enabled (once per sheet, after all pages placed)
        # Pass margin_pt so marks are positioned OUTSIDE content area
        if registration_marks:
            draw_registration_marks_on_sheet(out_page, sheet_w, sheet_h, margin_pt)
        
        # Draw page labels if enabled
        if page_labels:
            import os
            filename = os.path.basename(input_path)
            layout_info = f"{nup}-Up on {sheet_preset}" if sheet_preset != "Custom" else f"{nup}-Up Custom"
            draw_page_labels(out_page, sheet_w, sheet_h, margin_pt,
                           sheet_idx + 1, num_sheets, filename, layout_info)
    
    # Final progress update
    if progress_callback:
        progress_callback(num_sheets, num_sheets)
    
    # Save output document
    out_doc.save(output_path, garbage=4, deflate=True)
    out_doc.close()
    src_doc.close()
    
    return num_sheets


def calculate_booklet_page_order(num_pages: int) -> List[Tuple[int, int]]:
    """
    Calculate page order for saddle-stitch booklet.
    
    Returns list of (left_page, right_page) tuples for each side of each sheet.
    Page numbers are 0-based indices, -1 means blank.
    
    For 8 pages, the order is:
    - Sheet 1 front: (7, 0)  -> pages 8, 1
    - Sheet 1 back:  (1, 6)  -> pages 2, 7
    - Sheet 2 front: (5, 2)  -> pages 6, 3
    - Sheet 2 back:  (3, 4)  -> pages 4, 5
    """
    # Pad to multiple of 4
    padded = ((num_pages + 3) // 4) * 4
    
    pages = []
    left = 0
    right = padded - 1
    
    while left < right:
        # Front of sheet: right page on left, left page on right
        pages.append((right, left))
        left += 1
        right -= 1
        
        # Back of sheet: left page on left, right page on right
        pages.append((left, right))
        left += 1
        right -= 1
    
    # Convert indices >= num_pages to -1 (blank)
    result = []
    for left_idx, right_idx in pages:
        l = left_idx if left_idx < num_pages else -1
        r = right_idx if right_idx < num_pages else -1
        result.append((l, r))
    
    return result


def impose_booklet(
    input_path: str,
    output_path: str,
    sheet_preset: str = "A3",
    page_range_expr: Optional[str] = None,
    margin_mm: float = 0.0,
    gap_mm: float = 0.0,
    orientation: str = "landscape",
    crop_marks: bool = False,
    registration_marks: bool = False,
    page_labels: bool = False,
    custom_size_mm: Optional[Tuple[float, float]] = None,
    progress_callback: Optional[callable] = None,
) -> int:
    """
    Create saddle-stitch booklet PDF using vector placement.
    
    Reorders pages so when printed double-sided, folded, and stapled,
    pages read in correct order. Auto-pads to multiple of 4 pages.
    
    Args:
        input_path: Path to input PDF file
        output_path: Path for output booklet PDF
        sheet_preset: Output sheet size ("A3", "A4", "Letter", "Tabloid")
        page_range_expr: Page range expression (1-based, e.g., "1-4,7,10-12")
                        If None, all pages are used
        margin_mm: Margin around sheet edge in millimeters
        gap_mm: Gap between pages in millimeters
        orientation: Sheet orientation ("landscape" or "portrait")
        crop_marks: Whether to draw crop marks around each page
        registration_marks: Whether to draw registration marks on sheet
        page_labels: Whether to draw page labels in margins
        custom_size_mm: Custom sheet size (width, height) in mm, overrides preset
        progress_callback: Optional callback(current, total) for progress updates
        
    Returns:
        Number of output sides (pages in output PDF)
    """
    # Get sheet dimensions in points
    if custom_size_mm:
        w_pt = mm_to_pt(custom_size_mm[0])
        h_pt = mm_to_pt(custom_size_mm[1])
        # Apply orientation
        if orientation == "landscape":
            sheet_w, sheet_h = max(w_pt, h_pt), min(w_pt, h_pt)
        else:
            sheet_w, sheet_h = min(w_pt, h_pt), max(w_pt, h_pt)
    else:
        sheet_w, sheet_h = get_sheet_size_pt(sheet_preset, orientation)
    
    # Convert margins and gaps to points
    margin_pt = mm_to_pt(margin_mm)
    gap_pt = mm_to_pt(gap_mm)
    
    # 2-up layout (2 columns, 1 row)
    cols, rows = 2, 1
    
    # Calculate cell dimensions
    available_w = sheet_w - 2 * margin_pt - (cols - 1) * gap_pt
    available_h = sheet_h - 2 * margin_pt - (rows - 1) * gap_pt
    
    cell_w = available_w / cols
    cell_h = available_h / rows
    
    if cell_w <= 0 or cell_h <= 0:
        raise ValueError(
            f"Margins and gaps too large for sheet size. "
            f"Cell size would be {cell_w:.1f}x{cell_h:.1f} points"
        )
    
    # Open input document
    src_doc = fitz.open(input_path)
    total_pages = len(src_doc)
    
    if total_pages == 0:
        src_doc.close()
        raise ValueError("Input PDF has no pages")
    
    # Determine which pages to include
    if page_range_expr is None:
        page_indices = list(range(total_pages))
    else:
        page_indices = parse_page_range(page_range_expr, total_pages)
    
    num_source_pages = len(page_indices)
    
    # Calculate booklet page order
    booklet_order = calculate_booklet_page_order(num_source_pages)
    num_sides = len(booklet_order)
    
    # Create output document
    out_doc = fitz.open()
    
    # Process each side (front/back of each sheet)
    for side_idx, (left_page, right_page) in enumerate(booklet_order):
        # Report progress
        if progress_callback:
            progress_callback(side_idx, num_sides)
        
        # Create new page with sheet dimensions
        out_page = out_doc.new_page(width=sheet_w, height=sheet_h)
        
        # Place left page
        left_rect = None
        if left_page >= 0:
            src_page_idx = page_indices[left_page]
            x0 = margin_pt
            y0 = margin_pt
            x1 = x0 + cell_w
            y1 = y0 + cell_h
            left_rect = fitz.Rect(x0, y0, x1, y1)
            
            out_page.show_pdf_page(
                left_rect,
                src_doc,
                src_page_idx,
                keep_proportion=True,
                overlay=True,
            )
        
        # Place right page
        right_rect = None
        if right_page >= 0:
            src_page_idx = page_indices[right_page]
            x0 = margin_pt + cell_w + gap_pt
            y0 = margin_pt
            x1 = x0 + cell_w
            y1 = y0 + cell_h
            right_rect = fitz.Rect(x0, y0, x1, y1)
            
            out_page.show_pdf_page(
                right_rect,
                src_doc,
                src_page_idx,
                keep_proportion=True,
                overlay=True,
            )
        
        # Draw crop marks if enabled
        if crop_marks:
            if left_rect:
                draw_crop_marks(out_page, left_rect)
            if right_rect:
                draw_crop_marks(out_page, right_rect)
        
        # Draw registration marks if enabled (positioned OUTSIDE content area)
        if registration_marks:
            draw_registration_marks_on_sheet(out_page, sheet_w, sheet_h, margin_pt)
        
        # Draw page labels if enabled
        if page_labels:
            import os
            filename = os.path.basename(input_path)
            # For booklet, show sheet and side info
            sheet_num = side_idx // 2 + 1
            side_name = "Front" if side_idx % 2 == 0 else "Back"
            preset_label = sheet_preset if sheet_preset != "Custom" else "Custom"
            layout_info = f"Booklet on {preset_label} - Sheet {sheet_num} {side_name}"
            draw_page_labels(out_page, sheet_w, sheet_h, margin_pt,
                           side_idx + 1, num_sides, filename, layout_info)
    
    # Final progress update
    if progress_callback:
        progress_callback(num_sides, num_sides)
    
    # Save output document
    out_doc.save(output_path, garbage=4, deflate=True)
    out_doc.close()
    src_doc.close()
    
    return num_sides
