# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['desktop_app.py'],
    pathex=[],
    binaries=[],
    datas=[('static', 'static'), ('LICENSE', '.')],
    # Modules imported only inside functions: static analysis can miss them
    # and they would be left out of the build.
    hiddenimports=['brand', 'connections', 'auth', 'billing', 'config', 'trends',
                   'licensing', 'own_app', 'version',
                   # Database access: WAL connections, schema versioning,
                   # backup. Listed to be safe even though it is imported
                   # normally, like the rest of this list.
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
    # UPX compresses the executable, but it is also the technique real
    # malware most often uses to obfuscate itself: many heuristic engines
    # (BitDefender, ALYac, GData, VIPRE...) flag any UPX-compressed, unsigned
    # binary regardless of what is inside it (measured: 9/57 on VirusTotal
    # for v1.5.0, all of them generic heuristic hits like
    # "Gen:Variant"/"Static AI", not one real family signature).
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
