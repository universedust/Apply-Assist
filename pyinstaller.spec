# pyinstaller.spec（修改后）
import os
import sys  # 新增导入sys模块

# 基础配置
block_cipher = None

# 收集依赖包
hiddenimports = [
    'openai', 'pdfplumber', 'docx2txt', 'jinja2', 'markupsafe',
    'cryptography.hazmat.primitives.asymmetric.ec',
    'cryptography.hazmat.primitives.hashes'
]

# 收集静态文件和环境变量
datas = [
    ('.env', '.'),
    ('uploads', 'uploads')
]

# 获取当前.spec文件的路径（替换__file__）
spec_file_path = os.path.dirname(os.path.abspath(sys.argv[0]))

# 主程序配置
a = Analysis(
    ['app.py'],
    pathex=[spec_file_path],  # 使用spec_file_path替代__file__
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 后续配置保持不变
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='留学助手后端',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True
)