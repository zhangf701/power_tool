#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerSystem Tool PyInstaller 打包脚本
--------------------------------------
自动修复 "_ctypes DLL load failed" 问题：
  程序运行前会扫描 base Python 的 DLLs 目录，
  把 _ctypes.pyd / libffi*.dll 显式写入 .spec 的 binaries，
  确保它们被打包进 .exe。

用法（在 power_tool/ 目录下运行）：
  python build.py
"""

import os
import sys
import subprocess
from pathlib import Path


# ---------------------------------------------------------------------------
# 1. 找到 base Python 安装目录（自动处理 venv）
# ---------------------------------------------------------------------------

def find_base_python_dir() -> Path:
    """返回 base Python 安装目录，自动识别 venv。"""
    python_exe = Path(sys.executable).resolve()

    # venv 中 python.exe 在 <venv>/Scripts/python.exe
    # pyvenv.cfg 在 <venv>/pyvenv.cfg
    search_parents = [
        python_exe.parent.parent,  # <venv> 根目录（若 exe 在 Scripts/）
        python_exe.parent,         # 直接父目录
    ]

    for parent in search_parents:
        cfg = parent / "pyvenv.cfg"
        if cfg.exists():
            for line in cfg.read_text(encoding="utf-8").splitlines():
                if line.lower().startswith("home"):
                    home = Path(line.split("=", 1)[1].strip())
                    # home 已是 base Python 根目录（含 python.exe）
                    return home

    # 非 venv：直接使用 python.exe 所在目录
    return python_exe.parent


# ---------------------------------------------------------------------------
# 2. 收集 _ctypes / libffi DLL
# ---------------------------------------------------------------------------

def collect_required_dlls(base_python_dir: Path) -> list:
    """收集所有运行时必须的 DLL。

    Miniconda 的 DLL 命名与标准 CPython 不同：
      - libffi-8.dll  ->  ffi-8.dll   （无 lib 前缀）
      - tk/tcl DLL    ->  Library/bin/
      - crypto/ssl    ->  Library/bin/
    搜索目录覆盖标准 Python 和 Miniconda 两种布局。
    """
    patterns = [
        # ctypes
        "_ctypes*.pyd",
        "libffi*.dll", "ffi*.dll",          # 标准 CPython / Miniconda 两种命名
        # tkinter（GUI 必须）
        "tk8*.dll", "tcl8*.dll",
        "_tkinter*.pyd",
        # 其他常见运行时
        "libcrypto*.dll",
        "libssl*.dll",
        "liblzma.dll",
        "libbz2.dll",
        "libexpat.dll",
    ]
    search_dirs = [
        base_python_dir / "DLLs",
        base_python_dir,
        base_python_dir / "Library" / "bin",               # Miniconda/Anaconda
        base_python_dir / "Library" / "mingw-w64" / "bin", # Miniconda/Anaconda
    ]

    found = []
    seen = set()
    for d in search_dirs:
        if not d.is_dir():
            continue
        for pat in patterns:
            for f in sorted(d.glob(pat)):
                if f.name not in seen:
                    found.append((str(f), "."))
                    seen.add(f.name)
                    print(f"       找到: {f}")
    return found


# ---------------------------------------------------------------------------
# 3. 生成 .spec 文件内容
# ---------------------------------------------------------------------------

def generate_spec(script_dir: Path, extra_binaries: list) -> str:
    entry    = str(script_dir / "power_tool.py")
    json_src = str(script_dir / "line_params_reference.json")

    datas = [(json_src, ".")]

    hidden = [
        # matplotlib
        "matplotlib.backends.backend_tkagg",
        "matplotlib.backends._backend_tk",
        "matplotlib.figure",
        "matplotlib.pyplot",
        # numpy
        "numpy",
        # tkinter
        "tkinter",
        "tkinter.ttk",
        "tkinter.messagebox",
        "tkinter.scrolledtext",
        # 本项目模块
        "power_tool_common",
        "power_tool_approximations",
        "power_tool_params",
        "power_tool_faults",
        "power_tool_stability",
        "power_tool_smib",
        "power_tool_line_geometry",
        "power_tool_loop_closure",
        "power_tool_gui",
    ]

    lines = [
        "# -*- mode: python ; coding: utf-8 -*-",
        "# 由 build.py 自动生成，请勿手工修改",
        "",
        "block_cipher = None",
        "",
        "a = Analysis(",
        f"    [{repr(entry)}],",
        f"    pathex=[{repr(str(script_dir))}],",
        f"    binaries={repr(extra_binaries)},",
        f"    datas={repr(datas)},",
        f"    hiddenimports={repr(hidden)},",
        "    hookspath=[],",
        "    runtime_hooks=[],",
        "    excludes=[],",
        "    cipher=block_cipher,",
        "    noarchive=False,",
        ")",
        "",
        "pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)",
        "",
        "exe = EXE(",
        "    pyz,",
        "    a.scripts,",
        "    a.binaries,",
        "    a.zipfiles,",
        "    a.datas,",
        "    [],",
        "    name='PowerSystemTool',",
        "    debug=False,",
        "    bootloader_ignore_signals=False,",
        "    strip=False,",
        "    upx=False,",          # upx 压缩有时会破坏 DLL，保持关闭
        "    console=False,",      # 纯 GUI，不弹命令行窗口
        "    disable_windowed_traceback=False,",
        "    target_arch=None,",
        "    codesign_identity=None,",
        "    entitlements_file=None,",
        ")",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# 4. 检查 PyInstaller 是否已安装
# ---------------------------------------------------------------------------

def ensure_pyinstaller() -> bool:
    try:
        import PyInstaller  # noqa: F401
        return True
    except ImportError:
        print("[!] 未找到 PyInstaller，正在自动安装...")
        ret = subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller"],
            check=False,
        )
        return ret.returncode == 0


# ---------------------------------------------------------------------------
# 5. 主流程
# ---------------------------------------------------------------------------

def main() -> int:
    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)

    print("=" * 58)
    print("  PowerSystem Tool  打包脚本")
    print("=" * 58)

    # 步骤 1：确认 PyInstaller 可用
    if not ensure_pyinstaller():
        print("[FAIL] PyInstaller 安装失败，请手动执行：pip install pyinstaller")
        return 1
    print("[OK] PyInstaller 已就绪")

    # 步骤 2：定位 base Python
    base_python = find_base_python_dir()
    print(f"[OK] Base Python 目录: {base_python}")

    # 步骤 3：收集所有必要 DLL
    required_bins = collect_required_dlls(base_python)
    if required_bins:
        print(f"[OK] 共找到 {len(required_bins)} 个 DLL，将强制打入包内：")
    else:
        print("[!!] 未找到任何 DLL，请检查 Miniconda 安装目录")
        print(f"     预期路径：{base_python / 'Library' / 'bin'}")
        print("     打包仍会继续，但 .exe 运行时可能报错")

    # 步骤 4：写 spec 文件
    spec_path = script_dir / "PowerSystemTool.spec"
    spec_path.write_text(generate_spec(script_dir, required_bins), encoding="utf-8")
    print(f"[OK] Spec 文件已生成: {spec_path.name}")

    # 步骤 5：运行 PyInstaller
    print("\n[>>] 开始打包，请稍候（首次较慢）...\n")
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--clean", str(spec_path)],
        cwd=script_dir,
    )

    print()
    if result.returncode == 0:
        exe_path = script_dir / "dist" / "PowerSystemTool.exe"
        print("=" * 58)
        print("  打包成功！")
        print(f"  输出: {exe_path}")
        print("=" * 58)
    else:
        print("=" * 58)
        print("  打包失败，请把上方完整输出发给 Claude 排查。")
        print("=" * 58)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
