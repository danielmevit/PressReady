from dataclasses import dataclass, field
from typing import List, Optional, Union
from enum import Enum

# --- Preprocessors ---

class PreprocessorType(Enum):
    REORDER_PAGES = "Reorder Pages"
    CLONE_PAGES = "Clone Pages"
    N_PLUS_1_PAGES = "N + 1 Pages"
    SPLIT_PAGES = "Split Pages"
    SHUFFLE_PAGES = "Shuffle Pages"
    RESIZE_PAGES = "Resize Pages"
    OVERRIDE_BOX = "Override Box"
    SETUP_BLEEDS = "Setup Bleeds"
    SCALE_PAGES = "Scale Pages"
    CENTER_AND_CROP = "Center and Crop"
    ROTATE_PAGES = "Rotate Pages"
    SLICE_PAGES = "Slice Pages"
    SCRIPT = "Script"

@dataclass
class PreprocessorStep:
    type: PreprocessorType
    enabled: bool = True
    params: dict = field(default_factory=dict)

# --- Layout ---

class LayoutType(Enum):
    N_UP = "N-Up"
    BOOKLET = "Booklet"
    # Add others as discovered: Cut & Stack, Step & Repeat, etc.

class BookletType(Enum):
    TWO_UP = "2-up"
    FOUR_UP = "4-up"

class BookletMode(Enum):
    SHEETWISE = "Sheetwise"
    WORK_AND_TURN = "Work and Turn"
    WORK_AND_TUMBLE = "Work and Tumble"
    PERFECT_BOUND = "Perfect Bound"

class CreepMode(Enum):
    SHIFT_BOTH = "Shift (move both edges)"
    SHIFT_IN = "Shift In"
    SHIFT_OUT = "Shift Out"
    SCALE = "Scale"

@dataclass
class LayoutSettings:
    type: LayoutType = LayoutType.BOOKLET
    
    # Common Parameters
    gutters_horizontal_mm: float = 0.0
    gutters_vertical_mm: float = 0.0
    
    # Booklet Specific
    booklet_type: BookletType = BookletType.TWO_UP
    booklet_mode: BookletMode = BookletMode.SHEETWISE
    right_to_left: bool = False
    move_fillers_to_middle: bool = False
    
    # Signatures
    signatures_enabled: bool = False
    signature_size_sheets: int = 1
    add_extra_pages: bool = False
    
    # Folding
    fold_in_parts: bool = False
    fold_part_size_sheets: int = 1
    
    # Page Creep
    creep_enabled: bool = False
    creep_mode: CreepMode = CreepMode.SHIFT_BOTH
    creep_shift_outer_mm: float = 0.0
    creep_shift_inner_mm: float = 0.0

# --- Marks ---

class MarkType(Enum):
    # Crop & Fold
    CROP_MARKS = "Crop Marks"
    GAP_CROP_MARKS = "Gap Crop Marks"
    PERFORATION_MARKS = "Perforation Marks"
    TRIM_LINE = "Trim Line"
    # Information
    TEXT = "Text"
    PLATE_NAMES = "Plate Names"
    BARCODE = "Barcode"
    # Color Bars
    COLOR_BAR_AUTO = "Color Bar (Auto)"
    COLOR_BAR_PDF = "Color Bar (PDF)"
    # Registration
    STAR_TARGET = "Star Target"
    BULL_EYE = "Bull Eye"
    # Booklet-specific
    FOLDING_MARKS = "Folding Marks"
    COLLATING_MARKS = "Collating Marks"
    # Other
    ANGLE_MARK = "Angle Mark"
    CUSTOM_MARK = "Custom Mark"

@dataclass
class MarkItem:
    type: MarkType
    enabled: bool = True
    params: dict = field(default_factory=dict)

# --- Sheet ---

@dataclass
class SheetSettings:
    width_mm: float = 297.0
    height_mm: float = 420.0
    margin_top_mm: float = 0.0
    margin_bottom_mm: float = 0.0
    margin_left_mm: float = 0.0
    margin_right_mm: float = 0.0
    duplex: bool = True

# --- Project ---

@dataclass
class Project:
    preprocessors: List[PreprocessorStep] = field(default_factory=list)
    layout: LayoutSettings = field(default_factory=LayoutSettings)
    sheet: SheetSettings = field(default_factory=SheetSettings)
    marks: List[MarkItem] = field(default_factory=list)
