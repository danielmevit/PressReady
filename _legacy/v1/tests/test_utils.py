"""
Tests for pressready.engine.utils module.
"""

import pytest
from pressready.engine.utils import mm_to_pt, pt_to_mm, parse_page_range


class TestUnitConversion:
    """Tests for unit conversion functions."""
    
    def test_mm_to_pt_zero(self):
        assert mm_to_pt(0) == 0
    
    def test_mm_to_pt_one_inch(self):
        # 25.4 mm = 1 inch = 72 points
        result = mm_to_pt(25.4)
        assert abs(result - 72.0) < 0.001
    
    def test_mm_to_pt_a4_width(self):
        # A4 width = 210 mm ≈ 595.28 points
        result = mm_to_pt(210)
        assert abs(result - 595.276) < 0.01
    
    def test_mm_to_pt_a4_height(self):
        # A4 height = 297 mm ≈ 841.89 points
        result = mm_to_pt(297)
        assert abs(result - 841.89) < 0.01
    
    def test_pt_to_mm_roundtrip(self):
        # Converting back and forth should preserve value
        original = 100.0
        converted = pt_to_mm(mm_to_pt(original))
        assert abs(converted - original) < 0.0001
    
    def test_pt_to_mm_72pt(self):
        # 72 points = 1 inch = 25.4 mm
        result = pt_to_mm(72)
        assert abs(result - 25.4) < 0.001


class TestParsePageRange:
    """Tests for page range parsing."""
    
    def test_single_page(self):
        result = parse_page_range("1", 10)
        assert result == [0]
    
    def test_single_page_middle(self):
        result = parse_page_range("5", 10)
        assert result == [4]
    
    def test_single_page_last(self):
        result = parse_page_range("10", 10)
        assert result == [9]
    
    def test_simple_range(self):
        result = parse_page_range("1-4", 10)
        assert result == [0, 1, 2, 3]
    
    def test_range_middle(self):
        result = parse_page_range("5-8", 10)
        assert result == [4, 5, 6, 7]
    
    def test_mixed_range_and_single(self):
        result = parse_page_range("1-4,7,10-12", 15)
        assert result == [0, 1, 2, 3, 6, 9, 10, 11]
    
    def test_whitespace_ignored(self):
        result = parse_page_range(" 1 - 3 , 5 ", 10)
        assert result == [0, 1, 2, 4]
    
    def test_multiple_singles(self):
        result = parse_page_range("1,3,5,7", 10)
        assert result == [0, 2, 4, 6]
    
    def test_multiple_ranges(self):
        result = parse_page_range("1-2,5-6,9-10", 10)
        assert result == [0, 1, 4, 5, 8, 9]
    
    # Error cases
    def test_error_empty_expression(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            parse_page_range("", 10)
    
    def test_error_whitespace_only(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            parse_page_range("   ", 10)
    
    def test_error_page_zero(self):
        with pytest.raises(ValueError, match="must be >= 1"):
            parse_page_range("0", 10)
    
    def test_error_negative_page(self):
        # "-1" is parsed as range "" to "1", which fails on empty string
        with pytest.raises(ValueError, match="Invalid"):
            parse_page_range("-1", 10)
    
    def test_error_page_exceeds_total(self):
        with pytest.raises(ValueError, match="exceeds document length"):
            parse_page_range("11", 10)
    
    def test_error_range_exceeds_total(self):
        with pytest.raises(ValueError, match="exceeds document length"):
            parse_page_range("8-12", 10)
    
    def test_error_invalid_range_start_greater_than_end(self):
        with pytest.raises(ValueError, match="start.*> end"):
            parse_page_range("5-3", 10)
    
    def test_error_invalid_page_number(self):
        with pytest.raises(ValueError, match="Invalid page number"):
            parse_page_range("abc", 10)
    
    def test_error_invalid_range_format(self):
        with pytest.raises(ValueError, match="Invalid"):
            parse_page_range("1-2-3", 10)
    
    def test_error_total_pages_zero(self):
        with pytest.raises(ValueError, match="total_pages must be >= 1"):
            parse_page_range("1", 0)
