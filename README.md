# 打印机耗材分配与费用分摊程序

## 功能特点

- ✅ **跨平台支持** - 兼容 Windows 7 和 macOS
- ✅ **图形界面** - 操作简单直观
- ✅ **耗材入库** - 记录采购的墨盒、硒鼓、纸张等
- ✅ **手动分配** - 指定耗材分配给特定部门
- ✅ **自动分摊** - 按部门人数/打印量比例自动计算费用
- ✅ **报表统计** - 生成部门费用汇总和明细报表
- ✅ **数据持久化** - 自动保存到本地 JSON 文件

## 系统要求

### Windows 7
- Python 3.7 或 3.8（Python 3.9+ 不支持 Windows 7）
- 下载地址：https://www.python.org/downloads/release/python-3810/

### macOS
- Python 3.7+（系统自带或官网下载）
- 支持 Intel 和 Apple Silicon Mac

## 安装方法

### 方法一：直接运行 Python 脚本

1. 安装 Python（勾选 "Add Python to PATH"）
2. 双击运行 `printer_supply_gui.py`
3. 或在命令行执行：
   ```bash
   python printer_supply_gui.py
   ```

### 方法二：打包成可执行文件（Windows）

如果不想安装 Python，可以打包成 exe：

```bash
# 安装打包工具
pip install pyinstaller

# 打包成单文件 exe
pyinstaller --onefile --windowed --name 耗材管理系统 printer_supply_gui.py

# 打包后的程序在 dist 文件夹中
```

打包后只需将 `耗材管理系统.exe` 和 `data.json` 一起分发即可。

## 使用说明

### 1. 耗材入库
- 点击「耗材入库」标签
- 填写耗材名称、类型、数量、单价
- 点击「入库」按钮
- 系统自动计算总成本

### 2. 耗材分配（手动）
- 点击「耗材分配」标签
- 选择要分配的耗材和部门
- 输入分配数量
- 点击「执行分配」

### 3. 自动按比例分摊
- 点击「自动分摊」标签
- 选择要分摊的耗材
- 输入各部门权重（如人数、预估打印量）
- 点击「开始自动分摊」
- 系统自动按权重比例分摊费用

### 4. 查看报表
- 点击「报表统计」标签
- 点击「刷新报表」
- 查看部门费用汇总和明细

### 5. 管理部门
- 点击「部门管理」标签
- 可添加新部门或删除现有部门

## 数据文件

程序会自动创建 `data.json` 文件存储所有数据，建议定期备份。

## 注意事项

1. Windows 7 用户请安装 Python 3.7 或 3.8，不要安装 3.9+
2. macOS 用户可能需要授予程序磁盘访问权限
3. 首次运行会自动创建示例部门数据

## 文件说明

- `printer_supply_gui.py` - 主程序
- `data.json` - 数据存储文件（自动生成）
