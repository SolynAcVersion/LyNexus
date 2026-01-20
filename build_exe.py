"""
Lynexus 打包脚本
快速打包命令: python build_exe.py
"""

import os
import sys
import subprocess

def main():
    """执行打包流程"""

    print("=" * 60)
    print("Lynexus 打包工具")
    print("=" * 60)

    # 检查是否安装了 PyInstaller
    try:
        import PyInstaller
        print(f"✓ PyInstaller 已安装: {PyInstaller.__version__}")
    except ImportError:
        print("✗ PyInstaller 未安装")
        print("正在安装 PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller 安装完成")

    # 检查 main.py 是否存在
    if not os.path.exists('main.py'):
        print("✗ 错误: 找不到 main.py 文件")
        print("  请在项目根目录运行此脚本")
        sys.exit(1)

    print("\n开始打包...")
    print("-" * 60)

    # 执行 PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",  # 清理之前的构建
        "lynexus.spec"
    ]

    try:
        subprocess.check_call(cmd)
        print("\n" + "=" * 60)
        print("✓ 打包完成!")
        print("=" * 60)
        print(f"可执行文件位置: {os.path.abspath('dist/Lynexus.exe')}")
        print("\n提示:")
        print("  1. 在 dist/ 文件夹中找到 Lynexus.exe")
        print("  2. 双击运行测试")
        print("  3. 如果遇到问题，请查看日志")
        print("=" * 60)

    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 60)
        print("✗ 打包失败")
        print("=" * 60)
        print(f"错误代码: {e.returncode}")
        print("\n常见问题:")
        print("  1. 确保在虚拟环境中运行")
        print("  2. 检查所有依赖是否已安装")
        print("  3. 查看上面的错误信息")
        sys.exit(1)

if __name__ == "__main__":
    main()
