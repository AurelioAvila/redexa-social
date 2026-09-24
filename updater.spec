# A separate executable that replaces the application's files.
#
# It has to be its own process because on Windows a running executable
# cannot overwrite itself. The manifest verifier imports cryptography's
# Ed25519 implementation; PyInstaller's cryptography hook collects its native
# bindings. The trusted key and version floor are bundled Python modules.
#
#   pyinstaller updater.spec --noconfirm
#
# The result (dist/updater.exe) is copied into the application's
# folder before the release zip is created.

a = Analysis(
    ['updater_bin/main.py'],
    pathex=[SPECPATH],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Only things genuinely not needed to move folders around and make
        # one local HTTP request.
        #
        # CAREFUL: this list is easy to break. An earlier version of it
        # excluded 'email', which looks obviously useless to an updater - but
        # urllib.request imports it, and the executable would not start at
        # all. An updater that does not start is worse than no updater. If
        # anything is added here, the end-to-end run against the real
        # executable has to be repeated, not just the tests.
        'tkinter', 'unittest', 'pydoc', 'doctest', 'pdb', 'difflib', 'sqlite3',
        # Runner/version import these only inside app-side functions, never
        # during standalone authentication or installation.
        'cache', 'db',
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
    name='updater',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # Console deliberately visible: if an update goes wrong, the user sees
    # what is happening instead of a window that vanished into nothing.
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
