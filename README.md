# SRDP - Steering Robot Data Processing Application

[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![GUI Framework](https://img.shields.io/badge/GUI-CustomTkinter-navy.svg)](https://github.com/TomSchimansky/CustomTkinter)
[![Data Engine](https://img.shields.io/badge/Data-Pandas%20%7C%20NumPy-orange.svg)](https://pandas.pydata.org/)
[![Signal Processing](https://img.shields.io/badge/Signal-SciPy%20%7C%20PyWavelets-brightgreen.svg)](https://scipy.org/)
[![Export Engine](https://img.shields.io/badge/Export-PowerPoint%20%7C%20Excel-green.svg)](https://python-pptx.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

**SRDP (Steering Robot Data Processing)** is a high-performance, professional desktop application built with Python and CustomTkinter designed for automotive engineers, testing specialists, and vehicle dynamics researchers. It provides a modern GUI workflow to import, parse, filter, visualize, analyze, and report telemetry data collected from steering robots and vehicle sensor suites.

---

## 📋 Table of Contents

- [Key Features](#-key-features)
- [Supported Data Formats](#-supported-data-formats)
- [Project Architecture](#-project-architecture)
- [Signal Processing & Filtering](#-signal-processing--filtering)
- [Installation & Setup](#-installation--setup)
- [Usage Guide](#-usage-guide)
- [Automated PowerPoint & Excel Reporting](#-automated-powerpoint--excel-reporting)
- [Executable Building (PyInstaller)](#-executable-building-pyinstaller)
- [Configuration](#-configuration)
- [Contributing](#-contributing)
- [License & Author](#-license--author)

---

## ✨ Key Features

- **🚀 Multi-Format Telemetry Parsing**: Seamlessly import proprietary automotive logs, text tables, spreadsheets, JSON, and standard CSV datasets.
- **⚡ Fast Multi-Dataset Tagging & Ingestion**: Manage multiple test runs simultaneously, assign custom legend tags, and compare overlay telemetry in real-time.
- **📈 Advanced Signal Filtering & Denoising**: Filter noisy steering angle, torque, frequency, and acceleration telemetry using Butterworth, Elliptic, Savitzky-Golay, Median, 1D Kalman, Notch, and Wavelet Denoising algorithms.
- **📊 Interactive Multi-Axis Visualization**: Plot multi-channel signals on shared or dual Y-axes with interactive zoom, pan, grid controls, custom color palettes, and line weights.
- **🎯 Special Hardware Support**: Out-of-the-box support for proprietary steering robot test file structures including `.stmf` (Steering Test Master File) and `.xtrp`.
- **📄 Automated Presentation & Spreadsheet Reports**: Export interactive plot figures and tabulated summaries directly into formatted PowerPoint presentations (`.pptx`) or Excel spreadsheets (`.xlsx`).
- **🌙 Theme Customization**: Native Light, Dark, and System appearance modes with user-configurable color palettes.

---

## 📁 Supported Data Formats

| Category | File Extensions | Description |
| :--- | :--- | :--- |
| **Proprietary Automotive** | `.stmf`, `.xtrp` | Steering Test Master Files and XTRP telemetry files |
| **Delimited Text & Logs** | `.csv`, `.txt`, `.tsv`, `.tab`, `.dat`, `.log`, `.asc`, `.prn`, `.data` | Automatic delimiter detection (comma, semicolon, tab, pipe, whitespace) and auto-encoding detection (UTF-8, UTF-16, CP1252, ISO-8859-1) |
| **Spreadsheets** | `.xlsx`, `.xlsm`, `.xltx`, `.xltm`, `.xls`, `.xlsb`, `.ods` | Excel Workbooks, Binary Spreadsheets, OpenDocument Spreadsheets |
| **Structured Data** | `.json`, `.jsonl`, `.ndjson`, `.html`, `.htm` | Line-delimited JSON and HTML tabular extracts |

---

## 🏗️ Project Architecture

```
SRDP/
├── SRDP_App/
│   ├── main.py                     # Application entry point with Tcl/Tk runtime init & splash screen
│   ├── requirements.txt            # Python dependencies
│   ├── settings.json               # Persisted application configuration
│   ├── Temp.pptx                   # PowerPoint report master template
│   ├── SRDP_Pro.spec               # PyInstaller standalone executable specification
│   ├── SRDP_Professional.spec      # Alternative PyInstaller specification
│   │
│   ├── core/                       # Core Business Logic & Data Processing
│   │   ├── __init__.py
│   │   ├── data_manager.py         # Multi-format data loader, table conversion & dataframe cleaner
│   │   └── settings_manager.py     # Settings load/save and app directory resolution
│   │
│   └── ui/                         # CustomTkinter GUI Components
│       ├── __init__.py
│       ├── app_window.py           # Main window layout, navigation sidebar, top bar
│       ├── upload_frame.py         # File drag-and-drop / upload manager & table preview
│       ├── config_frame.py         # Axis selection & graph configuration
│       ├── graph_frame.py          # Interactive Matplotlib canvas, signal filters, PPT/Excel export
│       └── settings_frame.py       # Theme, line width, rolling average & color palette controls
│
├── .gitignore                      # Git ignore rules
├── README.md                       # Documentation
├── CONTRIBUTING.md                 # Contribution guidelines
└── LICENSE                         # MIT License
```

---

## 🔬 Signal Processing & Filtering

SRDP includes an engineering-grade suite of digital signal processing algorithms designed to clean high-frequency sensor noise from steering angle, torque, force, and velocity measurements:

1. **Butterworth Low-Pass Filter**: Smooths out high-frequency noise with zero phase distortion via `scipy.signal.filtfilt`.
2. **Elliptic Low-Pass Filter**: Sharp roll-off low-pass filtering with configurable passband ripple and stopband attenuation.
3. **Savitzky-Golay Filter**: Polynomial smoothing to preserve signal peak amplitudes and sharp directional transitions.
4. **Median Filter**: Removes impulsive spikes and dropouts from sensor telemetry.
5. **1D Kalman Filter**: State-estimation algorithm for real-time tracking under stochastic measurement noise.
6. **Notch Filter**: Band-stop filter specifically tailored to eliminate 50Hz / 60Hz powerline interference.
7. **Wavelet Denoising**: Discrete Wavelet Transform (PyWavelets) noise reduction.

---

## ⚙️ Installation & Setup

### Prerequisites
- **Python 3.9+** installed on your system.
- Git (optional, for cloning).

### 1. Clone the Repository
```bash
git clone https://github.com/gourav-saharan/SRDP.git
cd SRDP/SRDP_App
```

### 2. Create & Activate Virtual Environment (Recommended)
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🚀 Usage Guide

### Running the Application
Launch SRDP by running `main.py`:
```bash
python main.py
```

### Step-by-Step Workflow:
1. **Upload Telemetry Data (`🏠 Home`)**:
   - Click **Upload Files** or drag and drop supported test files (`.stmf`, `.csv`, `.xlsx`, `.txt`, etc.).
   - Assign custom **Legend Tags** for each test run to distinguish datasets.
   - Inspect loaded rows, columns, and data structures in the **Input Data Preview** table.
2. **Configure Graph Axes (`⚙️ Config`)**:
   - Select the desired **X-Axis** (e.g., Time, Frequency, Sample Count, Steering Angle).
   - Select one or multiple **Y-Axes** channels (e.g., Steering Torque, Motor Current, Wheel Speed).
   - Click **Process & View Graph**.
3. **Analyze & Filter Telemetry (`📈 Graph`)**:
   - Use the interactive chart tools (Zoom, Pan, Reset).
   - Select and tune digital filters (Butterworth, Savitzky-Golay, Kalman, etc.).
   - Overlay multiple test runs for comparative dynamics evaluation.
4. **Export Reports**:
   - Click **Export to PPT** to automatically generate slide decks incorporating active graph figures and data summaries using `Temp.pptx`.
   - Click **Export to Excel** to export formatted data tables.
5. **Customize Appearance (`🔧 Settings`)**:
   - Adjust theme modes (Light/Dark/System), line weights, smoothing windows, and custom color palettes.

---

## 📦 Executable Building (PyInstaller)

To build a standalone Windows binary (`SRDP_Pro.exe`) with bundled Tcl/Tk runtime and dependencies:

```bash
cd SRDP_App
pyinstaller SRDP_Pro.spec
```

The output executable directory will be generated inside `SRDP_App/dist/SRDP_Pro/`.

---

## 🔧 Configuration

Application settings are saved in `settings.json` and loaded automatically upon startup. Key customizable settings include:
- `theme`: `"System"`, `"Dark"`, or `"Light"`
- `line_width`: Floating point line thickness (default: `1.0` or `1.5`)
- `rolling_average_window`: Integer smoothing window size
- `line_colors`: List of 10 hex color strings for multi-channel plotting

---

## 🤝 Contributing

Contributions are welcome! Please check out [CONTRIBUTING.md](CONTRIBUTING.md) for details on code standards, submitting pull requests, and filing issues.

---

## 📜 License & Author

Distributed under the **MIT License**. See [LICENSE](LICENSE) for more information.

### 👤 Author
- **Gourav Saharan**
- **Email**: [gouravsaharan2002@gmail.com](mailto:gouravsaharan2002@gmail.com)
- **GitHub**: [gourav-saharan](https://github.com/gourav-saharan)
