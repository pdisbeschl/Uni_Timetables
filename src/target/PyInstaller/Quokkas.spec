# -*- mode: python -*-

block_cipher = None


a = Analysis(['C:\\Users\\Paul Disbeschl\\Documents\\New folder (2)\\src\\src\\main\\python\\main.py'],
             pathex=['C:\\Users\\Paul Disbeschl\\Documents\\New folder (2)\\src\\target\\PyInstaller'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=['c:\\users\\paul disbeschl\\appdata\\local\\programs\\python\\python36\\venv\\lib\\site-packages\\fbs\\freeze\\hooks'],
             runtime_hooks=['C:\\Users\\Paul Disbeschl\\Documents\\New folder (2)\\src\\target\\PyInstaller\\fbs_pyinstaller_hook.py'],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='Quokkas',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          console=False , icon='C:\\Users\\Paul Disbeschl\\Documents\\New folder (2)\\src\\src\\main\\icons\\Icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='Quokkas')
