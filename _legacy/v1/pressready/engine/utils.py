"""
Utility functions for unit conversion and page range parsing.
"""

import re
from typing import List

# Conversion factor: 1 inch = 72 points, 1 inch = 25.4 mm
PT_PER_MM = 72.0 / 25.4  # ~2.834645669


def mm_to_pt(mm: float) -> float:
    """
    Convert millimeters to PDF points.
    
    Args:
        mm: Value in millimeters
        
    Returns:
        Value in PDF points (1 point = 1/72 inch)
    """
    return mm * PT_PER_MM


def pt_to_mm(pt: float) -> float:
    """
    Convert PDF points to millimeters.
    
    Args:
        pt: Value in PDF points
        
    Returns:
        Value in millimeters
    """
    return pt / PT_PER_MM


def parse_page_range(expr: str, total_pages: int) -> List[int]:
    """
    Parse a page range expression into a list of 0-based page indices.
    
    Supports:
    - Single pages: "1", "5"
    - Ranges: "1-4", "10-15"
    - Mixed: "1-4,7,10-12"
    - Whitespace is ignored
    
    Args:
        expr: Page range expression (1-based, e.g., "1-4,7,10-12")
        total_pages: Total number of pages in the document
        
    Returns:
        List of 0-based page indices
        
    Raises:
        ValueError: If expression is invalid or pages are out of bounds
    """
    if total_pages < 1:
        raise ValueError(f"total_pages must be >= 1, got {total_pages}")
    
    # Remove all whitespace
    expr = re.sub(r'\s+', '', expr)
    
    if not expr:
        raise ValueError("Page range expression cannot be empty")
    
    result = []
    parts = expr.split(',')
    
    for part in parts:
        if not part:
            continue
            
        if '-' in part:
            # Range: "1-4"
            range_parts = part.split('-')
            if len(range_parts) != 2:
                raise ValueError(f"Invalid range format: '{part}'")
            
            try:
                start = int(range_parts[0])
                end = int(range_parts[1])
            except ValueError:
                raise ValueError(f"Invalid page numbers in range: '{part}'")
            
            if start < 1:
                raise ValueError(f"Page number must be >= 1, got {start}")
            if end > total_pages:
                raise ValueError(f"Page {end} exceeds document length ({total_pages} pages)")
            if start > end:
                raise ValueError(f"Invalid range: start ({start}) > end ({end})")
            
            # Convert to 0-based indices
            result.extend(range(start - 1, end))
        else:
            # Single page: "7"
            try:
                page = int(part)
            except ValueError:
                raise ValueError(f"Invalid page number: '{part}'")
            
            if page < 1:
                raise ValueError(f"Page number must be >= 1, got {page}")
            if page > total_pages:
                raise ValueError(f"Page {page} exceeds document length ({total_pages} pages)")
            
            # Convert to 0-based index
            result.append(page - 1)
    
    if not result:
        raise ValueError("No valid pages in expression")
    
    return result
