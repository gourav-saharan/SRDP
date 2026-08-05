# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from importlib.util import find_spec
from PyInstaller.utils.hooks import collect_all

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
]
project_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
template_path = os.path.join(project_dir, 'Temp.pptx')
if os.path.exists(template_path):
    datas.append((template_path, '.'))

for package in ('customtkinter', 'openpyxl', 'xlrd', 'pyxlsb', 'odf', 'lxml', 'pptx'):
    if find_spec(package):
        tmp_ret = collect_all(package)
        datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

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
    [],
    exclude_binaries=True,
    name='SRDP_Pro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SRDP_Pro',
)
