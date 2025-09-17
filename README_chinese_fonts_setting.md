# 中文字体配置说明

## 问题描述

在使用 `view_chart.py` 显示交易图表时，由于标题和标签包含中文，可能会出现中文显示为方块（乱码）的问题。

## 解决方案

### 1. 安装必要的依赖

首先确保安装了所需的Python包：

```bash
pip3 install matplotlib pandas numpy ccxt
```

### 2. 中文字体配置

项目中已经添加了自动的中文字体配置功能：

- **`chinese_font_config.py`**: 专门的中文字体配置模块
- **`chart_viewer.py`**: 已集成中文字体配置
- **`cmd/view_chart.py`**: 已集成中文字体配置

### 3. 支持的字体

根据不同操作系统，会自动选择合适的中文字体：

#### macOS
- Arial Unicode MS (推荐)
- PingFang SC
- Heiti SC
- STHeiti

#### Windows
- SimHei (黑体)
- Microsoft YaHei (微软雅黑)
- SimSun (宋体)

#### Linux
- WenQuanYi Micro Hei (文泉驿微米黑)
- Noto Sans CJK SC
- DejaVu Sans

### 4. 测试中文字体

可以运行测试脚本来验证中文字体配置是否正确：

```bash
python3 chinese_font_config.py
```

或者：

```bash
python3 test_chinese_font.py
```

这会生成一个测试图片 `chinese_font_test.png`，检查其中的中文是否正确显示。

### 5. 使用图表查看器

现在可以正常使用图表查看器，中文应该能正确显示：

```bash
python3 cmd/view_chart.py
```

### 6. 故障排除

如果中文仍然显示为方块：

1. **检查系统字体**：确保系统安装了中文字体
2. **手动安装字体**：
   - macOS: 可以安装 Arial Unicode MS 或其他中文字体
   - Windows: 通常已经包含中文字体
   - Linux: 安装中文字体包，如 `sudo apt-get install fonts-wqy-microhei`

3. **查看日志**：运行程序时会显示使用的字体信息

### 7. 自定义字体

如果需要使用特定的中文字体，可以修改 `chinese_font_config.py` 中的字体列表。

## 技术细节

### 字体配置原理

1. 检测操作系统类型
2. 根据系统类型选择合适的中文字体候选列表
3. 检查系统中可用的字体
4. 设置 matplotlib 的字体参数
5. 配置负号显示以避免显示问题

### 配置参数

主要的matplotlib配置参数：

```python
plt.rcParams['font.sans-serif'] = [选择的中文字体, 备用字体...]
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
```

## 更新日志

- 添加了自动中文字体检测和配置
- 支持多操作系统的字体选择
- 添加了字体配置测试功能
- 改进了错误处理和用户提示
