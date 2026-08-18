# Eseguibile separato che sostituisce i file dell'applicazione.
#
# Deve essere un processo a se' perche' su Windows un eseguibile in
# esecuzione non puo' sovrascrivere se stesso. Usa solo la libreria
# standard, quindi resta piccolo e ha poche cose che possono mancare
# proprio nel momento in cui l'app non c'e' piu'.
#
#   pyinstaller updater.spec --noconfirm
#
# Il risultato (dist/updater/updater.exe) va copiato dentro la cartella
# dell'applicazione prima di creare lo zip della release.

a = Analysis(
    ['updater_bin/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Solo cose che non servono davvero a spostare cartelle e fare una
        # richiesta HTTP locale.
        #
        # ATTENZIONE: qui e' facile fare danni. Una versione precedente di
        # questo elenco escludeva 'email', che sembra ovviamente inutile per
        # un updater - ma urllib.request lo importa, e l'eseguibile non
        # partiva affatto. Un updater che non parte e' peggio di nessun
        # updater. Se si aggiunge qualcosa a questo elenco, va rieseguita la
        # prova end-to-end con l'eseguibile vero, non solo i test.
        'tkinter', 'unittest', 'pydoc', 'doctest', 'pdb', 'difflib', 'sqlite3',
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
    # Console visibile di proposito: se un aggiornamento va storto, l'utente
    # vede cosa sta succedendo invece di una finestra sparita nel nulla.
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
