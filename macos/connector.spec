block_cipher = None

a = Analysis(
    ["app.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("templates", "templates"),
        ("static", "static"),
        ("themes.json", "."),
        ("version.py", "."),
        ("moduller", "moduller"),
        ("moduller/moduller", "moduller/moduller"),
    ],
    hiddenimports=[
        "flask", "flask_cors", "flask_mail", "werkzeug",
        "jinja2", "markupsafe", "certifi",
        "charset_normalizer", "idna", "urllib3",
        "requests", "pymysql", "boto3", "botocore",
        "cryptography", "mss", "PIL",
        "psutil", "webview", "rumps",
        "dotenv", "openai",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "scipy"],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="connector",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="connector",
)