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
    # UPX comprime l'eseguibile, ma e' anche la tecnica piu' usata dai
    # malware reali per offuscarsi: molti motori euristici (BitDefender,
    # ALYac, GData, VIPRE...) flaggano qualsiasi binario compresso con UPX
    # e non firmato, indipendentemente dal contenuto (verificato: 9/57 su
    # VirusTotal per la v1.5.0, tutti rilevamenti euristici generici come
    # "Gen:Variant"/"Static AI", nessuna firma di famiglia reale).
    upx=False,
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
    upx=False,
    upx_exclude=[],
    name='Social Dashboard',
)
