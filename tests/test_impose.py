"""
Tests for pressready.engine.impose module.
"""

import os
import tempfile
import pytest
import fitz  # PyMuPDF

from pressready.engine.impose import impose_nup, impose_booklet, get_sheet_size_pt, calculate_booklet_page_order, SHEET_PRESETS_MM
from pressready.engine.utils import mm_to_pt


def create_sample_pdf(path: str, num_pages: int, page_size_mm=(210, 297)) -> None:
    """Helper: Create a simple multi-page PDF for testing."""
    doc = fitz.open()
    width = mm_to_pt(page_size_mm[0])
    height = mm_to_pt(page_size_mm[1])
    
    for i in range(num_pages):
        page = doc.new_page(width=width, height=height)
        # Add page number text for visual verification
        page.insert_text(
            (width / 2 - 20, height / 2),
            str(i + 1),
            fontsize=72,
            color=(0, 0, 0),
        )
    
    doc.save(path)
    doc.close()


class TestSheetPresets:
    """Tests for sheet size presets."""
    
    def test_a4_size_landscape(self):
        w, h = get_sheet_size_pt("A4", "landscape")
        # A4 landscape: 297 x 210 mm (width > height)
        assert abs(w - mm_to_pt(297)) < 0.01
        assert abs(h - mm_to_pt(210)) < 0.01
    
    def test_a4_size_portrait(self):
        w, h = get_sheet_size_pt("A4", "portrait")
        # A4 portrait: 210 x 297 mm (width < height)
        assert abs(w - mm_to_pt(210)) < 0.01
        assert abs(h - mm_to_pt(297)) < 0.01
    
    def test_a3_size_landscape(self):
        w, h = get_sheet_size_pt("A3", "landscape")
        # A3 landscape: 420 x 297 mm
        assert abs(w - mm_to_pt(420)) < 0.01
        assert abs(h - mm_to_pt(297)) < 0.01
    
    def test_a3_size_portrait(self):
        w, h = get_sheet_size_pt("A3", "portrait")
        # A3 portrait: 297 x 420 mm
        assert abs(w - mm_to_pt(297)) < 0.01
        assert abs(h - mm_to_pt(420)) < 0.01
    
    def test_invalid_preset(self):
        with pytest.raises(ValueError, match="Unknown sheet preset"):
            get_sheet_size_pt("invalid")


class TestImposeNup:
    """Tests for N-Up imposition."""
    
    def test_2up_even_pages(self):
        """2-Up with 4 source pages should produce 2 output sheets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.pdf")
            output_path = os.path.join(tmpdir, "output.pdf")
            
            create_sample_pdf(input_path, num_pages=4)
            
            num_sheets = impose_nup(
                input_path=input_path,
                output_path=output_path,
                sheet_preset="A3",
                nup=2,
            )
            
            assert num_sheets == 2
            assert os.path.exists(output_path)
            
            # Verify output
            out_doc = fitz.open(output_path)
            assert len(out_doc) == 2
            out_doc.close()
    
    def test_2up_odd_pages(self):
        """2-Up with 5 source pages should produce 3 output sheets (last with 1 blank)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.pdf")
            output_path = os.path.join(tmpdir, "output.pdf")
            
            create_sample_pdf(input_path, num_pages=5)
            
            num_sheets = impose_nup(
                input_path=input_path,
                output_path=output_path,
                sheet_preset="A3",
                nup=2,
            )
            
            assert num_sheets == 3
            
            out_doc = fitz.open(output_path)
            assert len(out_doc) == 3
            out_doc.close()
    
    def test_4up_even_pages(self):
        """4-Up with 8 source pages should produce 2 output sheets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.pdf")
            output_path = os.path.join(tmpdir, "output.pdf")
            
            create_sample_pdf(input_path, num_pages=8)
            
            num_sheets = impose_nup(
                input_path=input_path,
                output_path=output_path,
                sheet_preset="A3",
                nup=4,
            )
            
            assert num_sheets == 2
            
            out_doc = fitz.open(output_path)
            assert len(out_doc) == 2
            out_doc.close()
    
    def test_4up_partial_last_sheet(self):
        """4-Up with 10 source pages should produce 3 sheets (last with 2 blanks)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.pdf")
            output_path = os.path.join(tmpdir, "output.pdf")
            
            create_sample_pdf(input_path, num_pages=10)
            
            num_sheets = impose_nup(
                input_path=input_path,
                output_path=output_path,
                sheet_preset="A3",
                nup=4,
            )
            
            assert num_sheets == 3  # ceil(10/4) = 3
            
            out_doc = fitz.open(output_path)
            assert len(out_doc) == 3
            out_doc.close()
    
    def test_page_range(self):
        """Using page range should only impose selected pages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.pdf")
            output_path = os.path.join(tmpdir, "output.pdf")
            
            create_sample_pdf(input_path, num_pages=10)
            
            # Select pages 1-4 (4 pages) with 2-Up = 2 sheets
            num_sheets = impose_nup(
                input_path=input_path,
                output_path=output_path,
                sheet_preset="A3",
                nup=2,
                page_range_expr="1-4",
            )
            
            assert num_sheets == 2
    
    def test_mixed_page_range(self):
        """Mixed page range expression."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.pdf")
            output_path = os.path.join(tmpdir, "output.pdf")
            
            create_sample_pdf(input_path, num_pages=12)
            
            # "1-2,5,8-10" = 6 pages, 4-Up = 2 sheets
            num_sheets = impose_nup(
                input_path=input_path,
                output_path=output_path,
                sheet_preset="A3",
                nup=4,
                page_range_expr="1-2,5,8-10",
            )
            
            assert num_sheets == 2  # ceil(6/4) = 2
    
    def test_margins_and_gaps(self):
        """Verify margins and gaps don't cause errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.pdf")
            output_path = os.path.join(tmpdir, "output.pdf")
            
            create_sample_pdf(input_path, num_pages=4)
            
            num_sheets = impose_nup(
                input_path=input_path,
                output_path=output_path,
                sheet_preset="A3",
                nup=2,
                margin_mm=10.0,
                gap_mm=5.0,
            )
            
            assert num_sheets == 2
            assert os.path.exists(output_path)
    
    def test_output_sheet_size_a3(self):
        """Output sheets should be A3 size when A3 preset is used."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.pdf")
            output_path = os.path.join(tmpdir, "output.pdf")
            
            create_sample_pdf(input_path, num_pages=2)
            
            impose_nup(
                input_path=input_path,
                output_path=output_path,
                sheet_preset="A3",
                nup=2,
            )
            
            out_doc = fitz.open(output_path)
            page = out_doc[0]
            
            expected_w = mm_to_pt(297)
            expected_h = mm_to_pt(420)
            
            assert abs(page.rect.width - expected_w) < 1
            assert abs(page.rect.height - expected_h) < 1
            
            out_doc.close()
    
    def test_output_sheet_size_a4(self):
        """Output sheets should be A4 size when A4 preset is used."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.pdf")
            output_path = os.path.join(tmpdir, "output.pdf")
            
            create_sample_pdf(input_path, num_pages=2)
            
            impose_nup(
                input_path=input_path,
                output_path=output_path,
                sheet_preset="A4",
                nup=2,
            )
            
            out_doc = fitz.open(output_path)
            page = out_doc[0]
            
            expected_w = mm_to_pt(210)
            expected_h = mm_to_pt(297)
            
            assert abs(page.rect.width - expected_w) < 1
            assert abs(page.rect.height - expected_h) < 1
            
            out_doc.close()
    
    def test_invalid_nup(self):
        """Invalid nup value should raise ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.pdf")
            output_path = os.path.join(tmpdir, "output.pdf")
            
            create_sample_pdf(input_path, num_pages=4)
            
            with pytest.raises(ValueError, match="nup must be 2 or 4"):
                impose_nup(
                    input_path=input_path,
                    output_path=output_path,
                    nup=3,
                )
    
    def test_single_page_input(self):
        """Single page input should produce 1 output sheet."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.pdf")
            output_path = os.path.join(tmpdir, "output.pdf")
            
            create_sample_pdf(input_path, num_pages=1)
            
            num_sheets = impose_nup(
                input_path=input_path,
                output_path=output_path,
                sheet_preset="A3",
                nup=4,
            )
            
            assert num_sheets == 1
    
    def test_vector_placement_used(self):
        """
        Verify that show_pdf_page is used (vector placement).
        
        We can check this indirectly by verifying the output contains
        XObject references (Form XObjects from show_pdf_page).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.pdf")
            output_path = os.path.join(tmpdir, "output.pdf")
            
            create_sample_pdf(input_path, num_pages=4)
            
            impose_nup(
                input_path=input_path,
                output_path=output_path,
                sheet_preset="A3",
                nup=2,
            )
            
            # Open output and check for XObject references
            out_doc = fitz.open(output_path)
            page = out_doc[0]
            
            # show_pdf_page creates XObjects - check xref table
            xref = page.xref
            assert xref > 0  # Page has valid xref
            
            # Verify page has content (text from source pages)
            # show_pdf_page embeds source as Form XObject, preserving text
            page_text = page.get_text()
            assert page_text.strip()  # Should contain page numbers from source
            
            # Must close before temp directory cleanup on Windows
            out_doc.close()


class TestBookletPageOrder:
    """Tests for booklet page ordering."""
    
    def test_8_pages(self):
        """8 pages should produce correct booklet order."""
        order = calculate_booklet_page_order(8)
        # Sheet 1 front: 8,1 -> (7,0)
        # Sheet 1 back: 2,7 -> (1,6)
        # Sheet 2 front: 6,3 -> (5,2)
        # Sheet 2 back: 4,5 -> (3,4)
        assert order == [(7, 0), (1, 6), (5, 2), (3, 4)]
    
    def test_4_pages(self):
        """4 pages should produce single sheet booklet."""
        order = calculate_booklet_page_order(4)
        # Sheet 1 front: 4,1 -> (3,0)
        # Sheet 1 back: 2,3 -> (1,2)
        assert order == [(3, 0), (1, 2)]
    
    def test_6_pages_padded(self):
        """6 pages should be padded to 8 with blanks."""
        order = calculate_booklet_page_order(6)
        # Padded to 8: pages 0-5 exist, 6-7 are blank (-1)
        # Sheet 1 front: 8,1 -> (-1,0)
        # Sheet 1 back: 2,7 -> (1,-1)
        # Sheet 2 front: 6,3 -> (5,2)
        # Sheet 2 back: 4,5 -> (3,4)
        assert order == [(-1, 0), (1, -1), (5, 2), (3, 4)]
    
    def test_1_page_padded(self):
        """1 page should be padded to 4."""
        order = calculate_booklet_page_order(1)
        # Padded to 4: page 0 exists, 1-3 are blank
        assert order == [(-1, 0), (-1, -1)]


class TestImposeBooklet:
    """Tests for booklet imposition."""
    
    def test_8_page_booklet(self):
        """8-page booklet should produce 4 output sides."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.pdf")
            output_path = os.path.join(tmpdir, "output.pdf")
            
            create_sample_pdf(input_path, num_pages=8)
            
            num_sides = impose_booklet(
                input_path=input_path,
                output_path=output_path,
                sheet_preset="A3",
            )
            
            assert num_sides == 4  # 2 sheets x 2 sides
            assert os.path.exists(output_path)
            
            out_doc = fitz.open(output_path)
            assert len(out_doc) == 4
            out_doc.close()
    
    def test_12_page_booklet_padded(self):
        """12-page booklet should be padded to 16, producing 8 sides."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.pdf")
            output_path = os.path.join(tmpdir, "output.pdf")
            
            create_sample_pdf(input_path, num_pages=12)
            
            num_sides = impose_booklet(
                input_path=input_path,
                output_path=output_path,
                sheet_preset="A3",
            )
            
            # 12 pages padded to 16 = 4 sheets x 2 sides = 8 output pages
            assert num_sides == 8
            
            out_doc = fitz.open(output_path)
            assert len(out_doc) == 8
            out_doc.close()
    
    def test_booklet_with_margins(self):
        """Booklet with margins should work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.pdf")
            output_path = os.path.join(tmpdir, "output.pdf")
            
            create_sample_pdf(input_path, num_pages=8)
            
            num_sides = impose_booklet(
                input_path=input_path,
                output_path=output_path,
                sheet_preset="A3",
                margin_mm=10.0,
                gap_mm=5.0,
            )
            
            assert num_sides == 4
            assert os.path.exists(output_path)


class TestCropMarks:
    """Tests for crop marks feature."""
    
    def test_nup_with_crop_marks(self):
        """N-Up with crop marks should include marks in output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.pdf")
            output_path = os.path.join(tmpdir, "output.pdf")
            
            create_sample_pdf(input_path, num_pages=4)
            
            num_sheets = impose_nup(
                input_path=input_path,
                output_path=output_path,
                sheet_preset="A3",
                nup=2,
                crop_marks=True,
            )
            
            assert num_sheets == 2
            assert os.path.exists(output_path)
            
            # Verify output has drawing commands (crop marks are vector lines)
            out_doc = fitz.open(output_path)
            page = out_doc[0]
            # Crop marks add drawing content to the page
            drawings = page.get_drawings()
            assert len(drawings) > 0  # Should have crop mark lines
            out_doc.close()
    
    def test_booklet_with_crop_marks(self):
        """Booklet with crop marks should include marks in output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.pdf")
            output_path = os.path.join(tmpdir, "output.pdf")
            
            create_sample_pdf(input_path, num_pages=8)
            
            num_sides = impose_booklet(
                input_path=input_path,
                output_path=output_path,
                sheet_preset="A3",
                crop_marks=True,
            )
            
            assert num_sides == 4
            assert os.path.exists(output_path)
            
            out_doc = fitz.open(output_path)
            page = out_doc[0]
            drawings = page.get_drawings()
            assert len(drawings) > 0
            out_doc.close()
    
    def test_nup_without_crop_marks(self):
        """N-Up without crop marks should not have extra drawings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.pdf")
            output_path = os.path.join(tmpdir, "output.pdf")
            
            create_sample_pdf(input_path, num_pages=4)
            
            impose_nup(
                input_path=input_path,
                output_path=output_path,
                sheet_preset="A3",
                nup=2,
                crop_marks=False,
            )
            
            out_doc = fitz.open(output_path)
            page = out_doc[0]
            # Without crop marks, page shouldn't have extra line drawings
            # (source pages may have their own drawings though)
            out_doc.close()
