# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files

datas = []
binaries = []
hiddenimports = [
    '_tkinter',
    'tkinter',
    'tkinter.constants',
    'tkinter.filedialog',
    'tkinter.font',
    'tkinter.messagebox',
    'tkinter.simpledialog',
    'tkinter.ttk',
    'openpyxl',
    'xlrd',
    'pyxlsb',
    'odf',
    'lxml',
    'pptx',
    'pywt',
    'scipy.signal',
    'scipy.ndimage',
]
project_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
template_path = os.path.join(project_dir, 'Temp.pptx')
if os.path.exists(template_path):
    datas.append((template_path, '.'))

datas += collect_data_files('customtkinter')

python_base = sys.base_prefix
tkinter_package = os.path.join(python_base, 'Lib', 'tkinter')
if os.path.isdir(tkinter_package):
    datas.append((tkinter_package, 'tkinter'))

tcl_base = os.path.join(python_base, 'tcl')
tcl_source = os.path.join(tcl_base, 'tcl8.6')
tk_source = os.path.join(tcl_base, 'tk8.6')
tix_source = os.path.join(tcl_base, 'tix8.4.3')
if os.path.isdir(tcl_source):
    datas.append((tcl_source, '_tcl_data'))
if os.path.isdir(tk_source):
    datas.append((tk_source, '_tk_data'))
if os.path.isdir(tix_source):
    datas.append((tix_source, os.path.join('tcl', 'tix8.4.3')))

for dll_name in ('tcl86t.dll', 'tk86t.dll'):
    dll_path = os.path.join(python_base, 'DLLs', dll_name)
    if os.path.exists(dll_path):
        binaries.append((dll_path, '.'))


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={'matplotlib': {'backends': ['TkAgg']}},
    runtime_hooks=[],
    excludes=[
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'IPython',
        'jupyter',
        'notebook',
        'onnx',
        'onnxruntime',
        'pydantic',
        'pytest',
        'rich',
        'skimage',
        'sklearn',
        'tensorflow',
        'torch',
        'torchaudio',
        'torchvision',
        'matplotlib.backends.backend_qtagg',
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.backends.backend_qt6agg',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SRDP_Professional',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
