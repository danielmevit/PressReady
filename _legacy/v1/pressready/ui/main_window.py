"""
Main application window for PressReady.

Stage 2: Full UI with previews, controls, and drag-drop support.
"""

import os
from typing import Optional, Tuple

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QStatusBar,
    QFileDialog,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QLineEdit,
    QGroupBox,
    QFormLayout,
    QSplitter,
    QScrollArea,
    QSizePolicy,
    QProgressDialog,
    QMessageBox,
    QSlider,
    QCheckBox,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize
from PyQt6.QtGui import QFont, QPixmap, QImage, QDragEnterEvent, QDropEvent

import fitz  # PyMuPDF

from pressready.engine.impose import impose_nup, impose_booklet, SHEET_PRESETS_MM
from pressready.engine.utils import mm_to_pt, parse_page_range


class ExportWorker(QThread):
    """Background worker for exporting imposed PDFs."""
    
    progress = pyqtSignal(int, int)  # current, total
    finished = pyqtSignal(int, str)  # num_sheets, output_path
    error = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._task = None
    
    def set_task(self, input_path: str, output_path: str, settings: dict):
        """Set the export task."""
        self._task = {
            "input_path": input_path,
            "output_path": output_path,
            "settings": settings,
        }
    
    def run(self):
        if not self._task:
            return
        
        try:
            settings = self._task["settings"]
            
            def progress_callback(current, total):
                self.progress.emit(current, total)
            
            layout_mode = settings.get("layout_mode", "nup")
            
            if layout_mode == "booklet":
                num_sheets = impose_booklet(
                    input_path=self._task["input_path"],
                    output_path=self._task["output_path"],
                    sheet_preset=settings["sheet_preset"],
                    page_range_expr=settings.get("page_range"),
                    margin_mm=settings["margin_mm"],
                    gap_mm=settings["gap_mm"],
                    orientation=settings.get("orientation", "landscape"),
                    crop_marks=settings.get("crop_marks", False),
                    registration_marks=settings.get("registration_marks", False),
                    page_labels=settings.get("page_labels", False),
                    custom_size_mm=settings.get("custom_size_mm"),
                    progress_callback=progress_callback,
                )
            else:
                num_sheets = impose_nup(
                    input_path=self._task["input_path"],
                    output_path=self._task["output_path"],
                    sheet_preset=settings["sheet_preset"],
                    nup=settings["nup"],
                    page_range_expr=settings.get("page_range"),
                    margin_mm=settings["margin_mm"],
                    gap_mm=settings["gap_mm"],
                    orientation=settings.get("orientation", "landscape"),
                    crop_marks=settings.get("crop_marks", False),
                    registration_marks=settings.get("registration_marks", False),
                    page_labels=settings.get("page_labels", False),
                    custom_size_mm=settings.get("custom_size_mm"),
                    progress_callback=progress_callback,
                )
            
            self.finished.emit(num_sheets, self._task["output_path"])
            
        except Exception as e:
            self.error.emit(str(e))


class PreviewWorker(QThread):
    """Background worker for rendering previews."""
    
    finished = pyqtSignal(QPixmap, str, int)  # pixmap, preview_type, total_pages
    error = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._task = None
        self._cancelled = False
    
    def set_task(self, task_type: str, **kwargs):
        """Set the rendering task."""
        self._task = {"type": task_type, **kwargs}
        self._cancelled = False
    
    def cancel(self):
        """Cancel current task."""
        self._cancelled = True
    
    def run(self):
        if not self._task or self._cancelled:
            return
        
        try:
            task_type = self._task["type"]
            
            if task_type == "source":
                pixmap, total = self._render_source_page(
                    self._task["pdf_path"],
                    self._task["page_index"],
                    self._task["dpi"],
                )
                if not self._cancelled:
                    self.finished.emit(pixmap, "source", total)
                    
            elif task_type == "sheet":
                pixmap, total = self._render_sheet_preview(
                    self._task["pdf_path"],
                    self._task["settings"],
                    self._task["dpi"],
                )
                if not self._cancelled:
                    self.finished.emit(pixmap, "sheet", total)
                    
        except Exception as e:
            if not self._cancelled:
                self.error.emit(str(e))
    
    def _render_source_page(self, pdf_path: str, page_index: int, dpi: int) -> Tuple[QPixmap, int]:
        """Render a single source page to pixmap."""
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        page = doc[page_index]
        
        # Render to pixmap
        mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        # Convert to QPixmap
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(img)
        
        doc.close()
        return pixmap, total_pages
    
    def _render_sheet_preview(self, pdf_path: str, settings: dict, dpi: int) -> Tuple[QPixmap, int]:
        """Render imposed sheet 1 preview."""
        import tempfile
        
        # Create temporary imposed PDF
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Get page range for preview (use all or specified range)
            page_range = settings.get("page_range") or None
            layout_mode = settings.get("layout_mode", "nup")
            sheet_index = settings.get("sheet_index", 0)
            
            if layout_mode == "booklet":
                impose_booklet(
                    input_path=pdf_path,
                    output_path=tmp_path,
                    sheet_preset=settings["sheet_preset"],
                    page_range_expr=page_range,
                    margin_mm=settings["margin_mm"],
                    gap_mm=settings["gap_mm"],
                    orientation=settings.get("orientation", "landscape"),
                    crop_marks=settings.get("crop_marks", False),
                    registration_marks=settings.get("registration_marks", False),
                    page_labels=settings.get("page_labels", False),
                    custom_size_mm=settings.get("custom_size_mm"),
                )
            else:
                impose_nup(
                    input_path=pdf_path,
                    output_path=tmp_path,
                    sheet_preset=settings["sheet_preset"],
                    nup=settings["nup"],
                    page_range_expr=page_range,
                    margin_mm=settings["margin_mm"],
                    gap_mm=settings["gap_mm"],
                    orientation=settings.get("orientation", "landscape"),
                    crop_marks=settings.get("crop_marks", False),
                    registration_marks=settings.get("registration_marks", False),
                    page_labels=settings.get("page_labels", False),
                    custom_size_mm=settings.get("custom_size_mm"),
                )
            
            # Render specified sheet
            doc = fitz.open(tmp_path)
            total_sheets = len(doc)
            
            # Clamp sheet_index to valid range
            sheet_index = max(0, min(sheet_index, total_sheets - 1))
            page = doc[sheet_index]
            
            mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(img)
            
            doc.close()
            
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass
        
        return pixmap, total_sheets


class PreviewLabel(QLabel):
    """Label for displaying preview with proper scaling."""
    
    def __init__(self, placeholder_text: str = "", parent=None):
        super().__init__(parent)
        self._pixmap = None
        self._placeholder_text = placeholder_text
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(200, 200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd;")
        self.setText(placeholder_text)
    
    def setPreviewPixmap(self, pixmap: QPixmap):
        """Set the preview pixmap with proper scaling."""
        self._pixmap = pixmap
        self._updateDisplay()
    
    def clearPreview(self):
        """Clear the preview."""
        self._pixmap = None
        self.setText(self._placeholder_text)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._pixmap:
            self._updateDisplay()
    
    def _updateDisplay(self):
        if self._pixmap:
            scaled = self._pixmap.scaled(
                self.size() - QSize(10, 10),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            super().setPixmap(scaled)


class MainWindow(QMainWindow):
    """
    PressReady main window.
    
    Stage 2: Full UI with file loading, previews, and controls.
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PressReady - PDF Imposition Tool")
        self.setMinimumSize(1024, 768)
        self.resize(1400, 900)
        
        # State
        self._pdf_path: Optional[str] = None
        self._pdf_doc: Optional[fitz.Document] = None
        self._current_source_page: int = 0
        self._current_sheet_page: int = 0  # For sheet preview navigation
        self._total_sheet_pages: int = 0
        self._preview_dpi: int = 120  # Balance quality/speed
        self._cached_imposed_path: Optional[str] = None  # Cache for sheet preview
        
        # Workers
        self._source_worker = PreviewWorker(self)
        self._source_worker.finished.connect(self._on_source_preview_ready)
        self._source_worker.error.connect(self._on_preview_error)
        
        self._sheet_worker = PreviewWorker(self)
        self._sheet_worker.finished.connect(self._on_sheet_preview_ready)
        self._sheet_worker.error.connect(self._on_preview_error)
        
        # Debounce timer for sheet preview
        self._sheet_debounce = QTimer(self)
        self._sheet_debounce.setSingleShot(True)
        self._sheet_debounce.setInterval(200)  # 200ms debounce
        self._sheet_debounce.timeout.connect(self._render_sheet_preview)
        
        # Export worker
        self._export_worker = ExportWorker(self)
        self._export_worker.progress.connect(self._on_export_progress)
        self._export_worker.finished.connect(self._on_export_finished)
        self._export_worker.error.connect(self._on_export_error)
        self._progress_dialog: Optional[QProgressDialog] = None
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        self._setup_ui()
        self._setup_statusbar()
        self._connect_signals()
    
    def _setup_ui(self):
        """Build the main UI layout."""
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Left panel: Controls
        left_panel = self._create_controls_panel()
        left_panel.setFixedWidth(280)
        main_layout.addWidget(left_panel)
        
        # Splitter for previews
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Center: Source preview
        source_panel = self._create_source_preview_panel()
        splitter.addWidget(source_panel)
        
        # Right: Sheet preview
        sheet_panel = self._create_sheet_preview_panel()
        splitter.addWidget(sheet_panel)
        
        splitter.setSizes([400, 500])
        main_layout.addWidget(splitter, stretch=1)
    
    def _create_controls_panel(self) -> QWidget:
        """Create the left control panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("PressReady")
        title.setFont(QFont("", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("PDF Imposition Tool")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: gray;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(10)
        
        # Load button
        self._load_btn = QPushButton("Load PDF...")
        self._load_btn.setMinimumHeight(36)
        layout.addWidget(self._load_btn)
        
        # File info
        self._file_label = QLabel("No file loaded")
        self._file_label.setWordWrap(True)
        self._file_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self._file_label)
        
        layout.addSpacing(10)
        
        # Layout settings group
        layout_group = QGroupBox("Layout Settings")
        layout_form = QFormLayout(layout_group)
        layout_form.setSpacing(8)
        
        # Layout mode selector
        self._layout_combo = QComboBox()
        self._layout_combo.addItems(["2-Up", "4-Up", "Booklet"])
        layout_form.addRow("Layout:", self._layout_combo)
        
        # Sheet size selector
        self._sheet_combo = QComboBox()
        self._sheet_combo.addItems(list(SHEET_PRESETS_MM.keys()) + ["Custom"])
        self._sheet_combo.setCurrentText("A3")
        layout_form.addRow("Sheet Size:", self._sheet_combo)
        
        # Custom size inputs (hidden by default)
        custom_size_widget = QWidget()
        custom_size_layout = QHBoxLayout(custom_size_widget)
        custom_size_layout.setContentsMargins(0, 0, 0, 0)
        custom_size_layout.setSpacing(5)
        
        self._custom_width_spin = QDoubleSpinBox()
        self._custom_width_spin.setRange(50, 1000)
        self._custom_width_spin.setValue(297)
        self._custom_width_spin.setSuffix(" mm")
        self._custom_width_spin.setToolTip("Sheet width")
        custom_size_layout.addWidget(self._custom_width_spin)
        
        custom_size_layout.addWidget(QLabel("×"))
        
        self._custom_height_spin = QDoubleSpinBox()
        self._custom_height_spin.setRange(50, 1000)
        self._custom_height_spin.setValue(420)
        self._custom_height_spin.setSuffix(" mm")
        self._custom_height_spin.setToolTip("Sheet height")
        custom_size_layout.addWidget(self._custom_height_spin)
        
        self._custom_size_widget = custom_size_widget
        self._custom_size_widget.setVisible(False)
        layout_form.addRow("", self._custom_size_widget)
        
        # Orientation selector
        self._orientation_combo = QComboBox()
        self._orientation_combo.addItems(["Landscape", "Portrait"])
        layout_form.addRow("Orientation:", self._orientation_combo)
        
        # Margin
        self._margin_spin = QDoubleSpinBox()
        self._margin_spin.setRange(0, 50)
        self._margin_spin.setValue(5.0)
        self._margin_spin.setSuffix(" mm")
        self._margin_spin.setSingleStep(1.0)
        layout_form.addRow("Margin:", self._margin_spin)
        
        # Gap
        self._gap_spin = QDoubleSpinBox()
        self._gap_spin.setRange(0, 50)
        self._gap_spin.setValue(5.0)
        self._gap_spin.setSuffix(" mm")
        self._gap_spin.setSingleStep(1.0)
        layout_form.addRow("Gap:", self._gap_spin)
        
        # Page range
        self._range_edit = QLineEdit()
        self._range_edit.setPlaceholderText("e.g., 1-4,7,10-12 (all if empty)")
        layout_form.addRow("Page Range:", self._range_edit)
        
        # Crop marks checkbox
        self._crop_marks_check = QCheckBox("Add crop marks")
        self._crop_marks_check.setToolTip("Draw cut marks at page corners")
        layout_form.addRow("", self._crop_marks_check)
        
        # Registration marks checkbox
        self._reg_marks_check = QCheckBox("Add registration marks")
        self._reg_marks_check.setToolTip("Draw alignment crosshairs on sheet edges")
        layout_form.addRow("", self._reg_marks_check)
        
        # Page labels checkbox
        self._page_labels_check = QCheckBox("Add page labels")
        self._page_labels_check.setToolTip("Show filename and sheet info in margins")
        layout_form.addRow("", self._page_labels_check)
        
        layout.addWidget(layout_group)
        
        layout.addStretch()
        
        # Export button
        self._export_btn = QPushButton("Export PDF...")
        self._export_btn.setMinimumHeight(36)
        self._export_btn.setEnabled(False)
        layout.addWidget(self._export_btn)
        
        return panel
    
    def _create_source_preview_panel(self) -> QWidget:
        """Create the source preview panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Source Preview")
        title.setFont(QFont("", 11, QFont.Weight.Bold))
        header.addWidget(title)
        
        self._source_page_label = QLabel("Page - / -")
        self._source_page_label.setStyleSheet("color: #666;")
        header.addStretch()
        header.addWidget(self._source_page_label)
        layout.addLayout(header)
        
        # Preview area
        self._source_preview = PreviewLabel("Load a PDF to preview")
        layout.addWidget(self._source_preview, stretch=1)
        
        # Navigation
        nav_layout = QHBoxLayout()
        self._prev_btn = QPushButton("◀")
        self._prev_btn.setFixedWidth(40)
        self._prev_btn.setEnabled(False)
        self._prev_btn.setToolTip("Previous page")
        nav_layout.addWidget(self._prev_btn)
        
        # Page slider
        self._source_slider = QSlider(Qt.Orientation.Horizontal)
        self._source_slider.setMinimum(0)
        self._source_slider.setMaximum(0)
        self._source_slider.setValue(0)
        self._source_slider.setEnabled(False)
        self._source_slider.setToolTip("Drag to navigate pages")
        nav_layout.addWidget(self._source_slider, stretch=1)
        
        self._next_btn = QPushButton("▶")
        self._next_btn.setFixedWidth(40)
        self._next_btn.setEnabled(False)
        self._next_btn.setToolTip("Next page")
        nav_layout.addWidget(self._next_btn)
        
        layout.addLayout(nav_layout)
        
        return panel
    
    def _create_sheet_preview_panel(self) -> QWidget:
        """Create the sheet preview panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Sheet Preview")
        title.setFont(QFont("", 11, QFont.Weight.Bold))
        header.addWidget(title)
        
        self._sheet_info_label = QLabel("(Sheet 1)")
        self._sheet_info_label.setStyleSheet("color: #666;")
        header.addStretch()
        header.addWidget(self._sheet_info_label)
        layout.addLayout(header)
        
        # Preview area
        self._sheet_preview = PreviewLabel("Imposed sheet preview")
        layout.addWidget(self._sheet_preview, stretch=1)
        
        # Sheet navigation
        sheet_nav_layout = QHBoxLayout()
        self._sheet_prev_btn = QPushButton("◀")
        self._sheet_prev_btn.setFixedWidth(40)
        self._sheet_prev_btn.setEnabled(False)
        self._sheet_prev_btn.setToolTip("Previous sheet")
        sheet_nav_layout.addWidget(self._sheet_prev_btn)
        
        # Sheet slider
        self._sheet_slider = QSlider(Qt.Orientation.Horizontal)
        self._sheet_slider.setMinimum(0)
        self._sheet_slider.setMaximum(0)
        self._sheet_slider.setValue(0)
        self._sheet_slider.setEnabled(False)
        self._sheet_slider.setToolTip("Drag to navigate sheets")
        sheet_nav_layout.addWidget(self._sheet_slider, stretch=1)
        
        self._sheet_next_btn = QPushButton("▶")
        self._sheet_next_btn.setFixedWidth(40)
        self._sheet_next_btn.setEnabled(False)
        self._sheet_next_btn.setToolTip("Next sheet")
        sheet_nav_layout.addWidget(self._sheet_next_btn)
        
        layout.addLayout(sheet_nav_layout)
        
        return panel
    
    def _setup_statusbar(self):
        """Setup the status bar."""
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._statusbar.showMessage("Ready - Drop a PDF or click Load PDF")
    
    def _connect_signals(self):
        """Connect UI signals to slots."""
        self._load_btn.clicked.connect(self._on_load_clicked)
        self._export_btn.clicked.connect(self._on_export_clicked)
        self._prev_btn.clicked.connect(self._on_prev_page)
        self._next_btn.clicked.connect(self._on_next_page)
        self._sheet_prev_btn.clicked.connect(self._on_prev_sheet)
        self._sheet_next_btn.clicked.connect(self._on_next_sheet)
        
        # Slider navigation
        self._source_slider.valueChanged.connect(self._on_source_slider_changed)
        self._sheet_slider.valueChanged.connect(self._on_sheet_slider_changed)
        
        # Settings changes trigger sheet preview update (and reset to sheet 1)
        self._layout_combo.currentIndexChanged.connect(self._on_settings_changed)
        self._sheet_combo.currentIndexChanged.connect(self._on_sheet_size_changed)
        self._orientation_combo.currentIndexChanged.connect(self._on_settings_changed)
        self._custom_width_spin.valueChanged.connect(self._on_settings_changed)
        self._custom_height_spin.valueChanged.connect(self._on_settings_changed)
        self._margin_spin.valueChanged.connect(self._on_settings_changed)
        self._gap_spin.valueChanged.connect(self._on_settings_changed)
        self._range_edit.textChanged.connect(self._on_settings_changed)
        self._crop_marks_check.stateChanged.connect(self._schedule_sheet_preview)
        self._reg_marks_check.stateChanged.connect(self._schedule_sheet_preview)
        self._page_labels_check.stateChanged.connect(self._schedule_sheet_preview)
    
    def _on_settings_changed(self):
        """Handle settings change - reset to sheet 1 and re-render."""
        self._current_sheet_page = 0
        self._sheet_slider.setValue(0)
        self._schedule_sheet_preview()
    
    def _on_sheet_size_changed(self):
        """Handle sheet size dropdown change."""
        is_custom = self._sheet_combo.currentText() == "Custom"
        self._custom_size_widget.setVisible(is_custom)
        self._on_settings_changed()
    
    def _on_source_slider_changed(self, value: int):
        """Handle source page slider change."""
        if value != self._current_source_page:
            self._current_source_page = value
            self._update_nav_buttons()
            self._render_source_preview()
    
    def _on_sheet_slider_changed(self, value: int):
        """Handle sheet slider change."""
        if value != self._current_sheet_page:
            self._current_sheet_page = value
            self._update_sheet_nav_buttons()
            self._render_sheet_preview()
    
    # --- Drag and Drop ---
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].toLocalFile().lower().endswith('.pdf'):
                event.acceptProposedAction()
                self._statusbar.showMessage("Drop PDF to load...")
                return
        event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop."""
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path.lower().endswith('.pdf'):
                self._load_pdf(path)
                event.acceptProposedAction()
                return
        event.ignore()
    
    def dragLeaveEvent(self, event):
        """Handle drag leave."""
        if self._pdf_path:
            self._statusbar.showMessage(f"Loaded: {os.path.basename(self._pdf_path)}")
        else:
            self._statusbar.showMessage("Ready - Drop a PDF or click Load PDF")
    
    # --- File Operations ---
    
    def _on_load_clicked(self):
        """Handle Load PDF button click."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open PDF",
            "",
            "PDF Files (*.pdf);;All Files (*)",
        )
        if path:
            self._load_pdf(path)
    
    def _load_pdf(self, path: str):
        """Load a PDF file."""
        try:
            # Close previous document
            if self._pdf_doc:
                self._pdf_doc.close()
            
            # Open new document
            self._pdf_doc = fitz.open(path)
            self._pdf_path = path
            self._current_source_page = 0
            
            # Update UI
            page_count = len(self._pdf_doc)
            filename = os.path.basename(path)
            self._file_label.setText(f"{filename}\n{page_count} page(s)")
            self._statusbar.showMessage(f"Loaded: {filename} ({page_count} pages)")
            
            # Enable controls
            self._export_btn.setEnabled(True)
            self._update_nav_buttons()
            
            # Render previews
            self._render_source_preview()
            self._schedule_sheet_preview()
            
        except Exception as e:
            self._statusbar.showMessage(f"Error loading PDF: {e}")
            self._file_label.setText(f"Error: {e}")
    
    # --- Preview Rendering ---
    
    def _render_source_preview(self):
        """Start rendering source page preview."""
        if not self._pdf_path:
            return
        
        self._source_worker.cancel()
        self._source_worker.wait()
        
        self._source_worker.set_task(
            "source",
            pdf_path=self._pdf_path,
            page_index=self._current_source_page,
            dpi=self._preview_dpi,
        )
        self._source_worker.start()
        
        # Update page label
        total = len(self._pdf_doc) if self._pdf_doc else 0
        self._source_page_label.setText(f"Page {self._current_source_page + 1} / {total}")
    
    def _schedule_sheet_preview(self):
        """Schedule sheet preview rendering with debounce."""
        if self._pdf_path:
            self._sheet_debounce.start()
    
    def _render_sheet_preview(self):
        """Start rendering sheet preview."""
        if not self._pdf_path:
            return
        
        self._sheet_worker.cancel()
        self._sheet_worker.wait()
        
        settings = self._get_current_settings()
        settings["sheet_index"] = self._current_sheet_page
        
        # Validate page range before rendering
        page_range = settings.get("page_range")
        if page_range:
            try:
                parse_page_range(page_range, len(self._pdf_doc))
            except ValueError as e:
                self._sheet_preview.clearPreview()
                self._sheet_info_label.setText(f"Invalid range: {e}")
                return
        
        self._sheet_info_label.setText("(Rendering...)")
        
        self._sheet_worker.set_task(
            "sheet",
            pdf_path=self._pdf_path,
            settings=settings,
            dpi=self._preview_dpi,
        )
        self._sheet_worker.start()
    
    def _get_current_settings(self) -> dict:
        """Get current imposition settings from UI."""
        layout_text = self._layout_combo.currentText()
        
        if layout_text == "Booklet":
            layout_mode = "booklet"
            nup = 2  # Booklet is always 2-up
        elif layout_text == "4-Up":
            layout_mode = "nup"
            nup = 4
        else:  # "2-Up"
            layout_mode = "nup"
            nup = 2
        
        page_range = self._range_edit.text().strip()
        orientation = self._orientation_combo.currentText().lower()  # "landscape" or "portrait"
        
        # Handle custom sheet size
        sheet_preset = self._sheet_combo.currentText()
        custom_size_mm = None
        if sheet_preset == "Custom":
            custom_size_mm = (self._custom_width_spin.value(), self._custom_height_spin.value())
        
        return {
            "layout_mode": layout_mode,
            "nup": nup,
            "sheet_preset": sheet_preset,
            "custom_size_mm": custom_size_mm,
            "orientation": orientation,
            "margin_mm": self._margin_spin.value(),
            "gap_mm": self._gap_spin.value(),
            "page_range": page_range if page_range else None,
            "crop_marks": self._crop_marks_check.isChecked(),
            "registration_marks": self._reg_marks_check.isChecked(),
            "page_labels": self._page_labels_check.isChecked(),
        }
    
    def _on_source_preview_ready(self, pixmap: QPixmap, preview_type: str, total_pages: int):
        """Handle source preview rendered."""
        self._source_preview.setPreviewPixmap(pixmap)
    
    def _on_sheet_preview_ready(self, pixmap: QPixmap, preview_type: str, total_pages: int):
        """Handle sheet preview rendered."""
        self._sheet_preview.setPreviewPixmap(pixmap)
        self._total_sheet_pages = total_pages
        
        # Update navigation
        self._update_sheet_nav_buttons()
        
        settings = self._get_current_settings()
        current = self._current_sheet_page + 1
        
        if settings["layout_mode"] == "booklet":
            self._sheet_info_label.setText(
                f"Sheet {current}/{total_pages} - Booklet on {settings['sheet_preset']} ({settings['orientation'].title()})"
            )
        else:
            self._sheet_info_label.setText(
                f"Sheet {current}/{total_pages} - {settings['nup']}-Up on {settings['sheet_preset']} ({settings['orientation'].title()})"
            )
    
    def _on_preview_error(self, error: str):
        """Handle preview error."""
        self._statusbar.showMessage(f"Preview error: {error}")
    
    # --- Navigation ---
    
    def _on_prev_page(self):
        """Go to previous source page."""
        if self._current_source_page > 0:
            self._current_source_page -= 1
            self._update_nav_buttons()
            self._render_source_preview()
    
    def _on_next_page(self):
        """Go to next source page."""
        if self._pdf_doc and self._current_source_page < len(self._pdf_doc) - 1:
            self._current_source_page += 1
            self._update_nav_buttons()
            self._render_source_preview()
    
    def _update_nav_buttons(self):
        """Update navigation button states and slider."""
        if self._pdf_doc:
            total = len(self._pdf_doc)
            self._prev_btn.setEnabled(self._current_source_page > 0)
            self._next_btn.setEnabled(self._current_source_page < total - 1)
            
            # Update slider without triggering signal
            self._source_slider.blockSignals(True)
            self._source_slider.setMaximum(total - 1)
            self._source_slider.setValue(self._current_source_page)
            self._source_slider.setEnabled(total > 1)
            self._source_slider.blockSignals(False)
        else:
            self._prev_btn.setEnabled(False)
            self._next_btn.setEnabled(False)
            self._source_slider.setEnabled(False)
    
    # --- Sheet Navigation ---
    
    def _on_prev_sheet(self):
        """Go to previous sheet."""
        if self._current_sheet_page > 0:
            self._current_sheet_page -= 1
            self._update_sheet_nav_buttons()
            self._render_sheet_preview()
    
    def _on_next_sheet(self):
        """Go to next sheet."""
        if self._current_sheet_page < self._total_sheet_pages - 1:
            self._current_sheet_page += 1
            self._update_sheet_nav_buttons()
            self._render_sheet_preview()
    
    def _update_sheet_nav_buttons(self):
        """Update sheet navigation button states and slider."""
        self._sheet_prev_btn.setEnabled(self._current_sheet_page > 0)
        self._sheet_next_btn.setEnabled(self._current_sheet_page < self._total_sheet_pages - 1)
        
        # Update slider without triggering signal
        self._sheet_slider.blockSignals(True)
        self._sheet_slider.setMaximum(max(0, self._total_sheet_pages - 1))
        self._sheet_slider.setValue(self._current_sheet_page)
        self._sheet_slider.setEnabled(self._total_sheet_pages > 1)
        self._sheet_slider.blockSignals(False)
    
    # --- Export ---
    
    def _on_export_clicked(self):
        """Handle Export PDF button click."""
        if not self._pdf_path:
            return
        
        # Suggest output filename
        base = os.path.splitext(os.path.basename(self._pdf_path))[0]
        settings = self._get_current_settings()
        
        if settings["layout_mode"] == "booklet":
            layout_suffix = "booklet"
        else:
            layout_suffix = f"{settings['nup']}up"
        
        # Determine sheet size label
        if settings["sheet_preset"] == "Custom" and settings["custom_size_mm"]:
            w, h = settings["custom_size_mm"]
            # Format as integers if whole numbers, otherwise 1 decimal
            w_str = f"{int(w)}" if w == int(w) else f"{w:.1f}"
            h_str = f"{int(h)}" if h == int(h) else f"{h:.1f}"
            sheet_label = f"{w_str}x{h_str}mm"
        else:
            sheet_label = settings["sheet_preset"]
        
        # Add marks indicators
        marks_suffix = ""
        if settings["crop_marks"]:
            marks_suffix += "_cm"
        if settings["registration_marks"]:
            marks_suffix += "_reg"
        
        suggested = f"{base}_{layout_suffix}_{sheet_label}{marks_suffix}.pdf"
        
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Imposed PDF",
            suggested,
            "PDF Files (*.pdf);;All Files (*)",
        )
        
        if path:
            self._export_pdf(path)
    
    def _export_pdf(self, output_path: str):
        """Export the imposed PDF in background with progress dialog."""
        settings = self._get_current_settings()
        
        # Create progress dialog
        self._progress_dialog = QProgressDialog(
            "Exporting imposed PDF...",
            "Cancel",
            0, 100,
            self,
        )
        self._progress_dialog.setWindowTitle("Exporting")
        self._progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress_dialog.setMinimumDuration(0)
        self._progress_dialog.setValue(0)
        self._progress_dialog.canceled.connect(self._on_export_cancelled)
        
        # Disable export button during export
        self._export_btn.setEnabled(False)
        self._statusbar.showMessage("Exporting...")
        
        # Start export worker
        self._export_worker.set_task(self._pdf_path, output_path, settings)
        self._export_worker.start()
    
    def _on_export_progress(self, current: int, total: int):
        """Handle export progress update."""
        try:
            if self._progress_dialog is not None and not self._progress_dialog.wasCanceled():
                percent = int((current / total) * 100) if total > 0 else 0
                self._progress_dialog.setValue(percent)
                self._progress_dialog.setLabelText(f"Processing sheet {current + 1} of {total}...")
        except (RuntimeError, AttributeError):
            # Dialog may have been closed/deleted - ignore
            pass
    
    def _on_export_finished(self, num_sheets: int, output_path: str):
        """Handle export completion."""
        try:
            if self._progress_dialog is not None:
                self._progress_dialog.setValue(100)
                self._progress_dialog.close()
        except (RuntimeError, AttributeError):
            pass
        finally:
            self._progress_dialog = None
        
        self._export_btn.setEnabled(True)
        self._statusbar.showMessage(
            f"Exported {num_sheets} sheet(s) to {os.path.basename(output_path)}"
        )
        
        # Show success message
        QMessageBox.information(
            self,
            "Export Complete",
            f"Successfully exported {num_sheets} sheet(s) to:\n{output_path}",
        )
    
    def _on_export_error(self, error: str):
        """Handle export error."""
        try:
            if self._progress_dialog is not None:
                self._progress_dialog.close()
        except (RuntimeError, AttributeError):
            pass
        finally:
            self._progress_dialog = None
        
        self._export_btn.setEnabled(True)
        self._statusbar.showMessage(f"Export error: {error}")
        
        QMessageBox.critical(
            self,
            "Export Error",
            f"Failed to export PDF:\n{error}",
        )
    
    def _on_export_cancelled(self):
        """Handle export cancellation."""
        # Note: We can't actually cancel mid-export with current implementation,
        # but we can at least close the dialog and re-enable the button
        self._export_btn.setEnabled(True)
        self._statusbar.showMessage("Export cancelled")
    
    def closeEvent(self, event):
        """Clean up on close."""
        self._source_worker.cancel()
        self._sheet_worker.cancel()
        self._source_worker.wait()
        self._sheet_worker.wait()
        self._export_worker.wait()
        
        if self._pdf_doc:
            self._pdf_doc.close()
        
        super().closeEvent(event)
