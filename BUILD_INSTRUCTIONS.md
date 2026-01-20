# Lynexus 打包说明

## 方法一: 使用快速打包脚本 (推荐)

```bash
# 1. 确保在虚拟环境中
# Windows:
.venv\Scripts\activate

# 2. 运行打包脚本
python build_exe.py
```

打包完成后，可执行文件在 `dist/Lynexus.exe`

---

## 方法二: 手动使用 PyInstaller

```bash
# 1. 安装 PyInstaller
pip install pyinstaller

# 2. 使用配置文件打包
pyinstaller --clean lynexus.spec

# 或者使用简单命令 (不推荐，功能较少)
pyinstaller --name="Lynexus" --windowed --one-dir main.py
```

---

## 打包选项说明

### `--one-dir` (文件夹模式 - 推荐)
- **优点**: 启动快，运行稳定
- **缺点**: 包含多个文件
- **输出**: `dist/Lynexus/` 文件夹

### `--onefile` (单文件模式)
- **优点**: 只有一个 exe 文件
- **缺点**: 启动慢，可能不稳定
- **使用**: 在 `lynexus.spec` 中将 `exe = EXE(...)` 改为单文件模式

---

## 打包前检查清单

- [ ] 在虚拟环境中激活
- [ ] 所有依赖已安装 (`pip install -r requirements.txt`)
- [ ] 项目可以正常运行 (`python main.py`)
- [ ] 关闭不必要的应用 (释放内存)

---

## 打包后测试

1. **基本测试**
   ```bash
   # 进入 dist 文件夹
   cd dist/Lynexus

   # 运行程序
   Lynexus.exe
   ```

2. **检查功能**
   - [ ] 程序能正常启动
   - [ ] UI 显示正常
   - [ ] AI 功能正常
   - [ ] 配置保存/加载正常
   - [ ] MCP 工具正常

---

## 常见问题

### 1. 找不到模块
**错误**: `ModuleNotFoundError: No module named 'xxx'`

**解决**: 在 `lynexus.spec` 的 `hiddenimports` 中添加模块名

### 2. 找不到数据文件
**错误**: `FileNotFoundError: config/xxx`

**解决**: 在 `lynexus.spec` 的 `datas` 中添加文件路径

### 3. 杀毒软件误报
**原因**: PyInstaller 打包的程序可能被误判为病毒

**解决**:
- 添加到杀毒软件白名单
- 或使用代码签名 (需要证书)

### 4. 文件太大
**优化方法**:
- 使用 `--exclude-module` 排除不需要的模块
- 在 `lynexus.spec` 中添加更多 `excludes`
- 使用 UPX 压缩 (已启用)

### 5. 运行时闪退
**调试方法**:
- 临时设置 `console=True` 查看错误信息
- 检查日志文件
- 在开发环境重现问题

---

## 高级配置

### 添加自定义图标
1. 准备 `.ico` 文件
2. 在 `lynexus.spec` 中取消注释:
   ```python
   icon='icon.ico'
   ```

### 添加版本信息
1. 创建版本信息文件 `version.txt`
2. 在 `lynexus.spec` 中添加:
   ```python
   version='version.txt'
   ```

### 单文件打包
修改 `lynexus.spec` 最后部分为:
```python
exe = EXE(
    pyz,
    a.scripts,
    [],
    name='Lynexus',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    onefile=True,  # 启用单文件模式
    # icon='icon.ico',
)
```

---

## 分发建议

### 安装包制作
使用 Inno Setup 或 NSIS 创建安装程序:
- 下载: https://jrsoftware.org/isdl.php
- 可以创建专业的安装程序
- 支持卸载、开始菜单快捷方式等

### 压缩分发
```bash
# 使用 7-Zip 压缩
# 右键 dist/Lynexus 文件夹 -> 7-Zip -> 添加到压缩包
# 选择 "7z" 格式，"极限" 压缩
```

---

## 文件说明

- `lynexus.spec` - PyInstaller 配置文件
- `build_exe.py` - 快速打包脚本
- `BUILD_INSTRUCTIONS.md` - 本说明文档

---

## 获取帮助

如果遇到问题:
1. 查看上面的常见问题
2. 检查 PyInstaller 官方文档: https://pyinstaller.org/
3. 提交 Issue: https://github.com/SolynAcVersion/LyNexus/issues
