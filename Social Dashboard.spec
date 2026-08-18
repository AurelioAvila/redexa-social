# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['desktop_app.py'],
    pathex=[],
    binaries=[],
    datas=[('static', 'static'), ('LICENSE', '.')],
    # Moduli importati solo dentro le funzioni: l'analisi statica puo' non
    # accorgersene e finirebbero fuori dalla build.
    hiddenimports=['brand', 'connections', 'auth', 'billing', 'config', 'trends',
                   'licensing', 'own_app', 'version',
                   # Accesso al database: connessioni con WAL, versionamento
                   # dello schema, backup. Elencato per sicurezza anche se
                   # importato normalmente, come il resto di questa lista.
                   'db', 'db.connection', 'db.migrations', 'db.backup',
                   'secrets_store'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Social Dashboard',
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
    icon=['icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Social Dashboard',
)
