import sys
import os
import traceback

def run_check():
    print("="*50)
    print("  Power System Tool - 预发布环境检查 (Deploy Check)")
    print("="*50)

    # 1. 检查 Python 版本
    print(f"[*] 当前 Python 版本: {sys.version.split()[0]}")
    if sys.version_info < (3, 10):
        print("[!] 警告: 建议使用 Python 3.10 或以上版本。")
    else:
        print("[OK] 版本符合要求。")

    # 2. 检查核心第三方库
    dependencies = ['numpy', 'matplotlib', 'tkinter']
    print("\n[*] 正在检查第三方依赖库...")
    for lib in dependencies:
        try:
            __import__(lib)
            print(f"  [OK] {lib} 已安装")
        except ImportError:
            print(f"  [FAIL] 缺失库: {lib}。请运行: pip install {lib}")

    # 3. 检查项目内核模块 (按文件名导入)
    core_modules = [
        'power_tool_common',
        'power_tool_approximations',
        'power_tool_params',
        'power_tool_loop_closure',
        'power_tool_faults',
        'power_tool_smib',
        'power_tool_stability'
    ]
    print("\n[*] 正在检查项目内核模块...")
    for mod in core_modules:
        try:
            __import__(mod)
            print(f"  [OK] 模块 {mod} 载入正常")
        except Exception:
            print(f"  [FAIL] 模块 {mod} 载入异常！详情如下:")
            traceback.print_exc()

    # 4. 验证 JSON 数据库加载 (测试打包路径兼容性)
    print("\n[*] 正在验证数据文件加载 (JSON)...")
    try:
        from power_tool_common import load_line_params_reference
        data = load_line_params_reference()
        sections = data.get("sections", [])
        print(f"  [OK] 成功读取典型参数数据库，包含 {len(sections)} 个电压等级数据。")
    except Exception as e:
        print(f"  [FAIL] 无法加载 line_params_reference.json: {e}")

    print("\n" + "="*50)
    print("  检查完毕！如果上方全是 [OK]，即可放心打包。")
    print("="*50)

if __name__ == "__main__":
    run_check()
