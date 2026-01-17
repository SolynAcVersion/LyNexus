# Markdown 和 LaTeX 渲染功能

## 功能概述

现在聊天界面支持完整的 Markdown 和 LaTeX 公式渲染，包括：

### 支持的 Markdown 语法

- **标题**: `# H1`, `## H2`, `### H3` 等
- **粗体**: `**粗体文本**`
- **斜体**: `*斜体文本*`
- **代码块**:
  ```
  ```python
  def hello():
      print("Hello")
  ```
  ```
- **行内代码**: `` `代码` ``
- **列表**:
  - 无序列表: `- 项目`
  - 有序列表: `1. 项目`
- **表格**:
  ```markdown
  | 列1 | 列2 |
  |-----|-----|
  | 内容1 | 内容2 |
  ```
- **引用**: `> 引用文本`
- **链接**: `[文本](URL)`
- **水平线**: `---`

### 支持的 LaTeX 语法

- **行内公式**: `$E = mc^2$`
- **块级公式**:
  ```latex
  $$
  \sum_{i=1}^{n} i = \frac{n(n+1)}{2}
  $$
  ```

## 渲染模式

### 1. 非流式输出（完整渲染）

对于非流式输出，完整的响应会在接收完成后一次性渲染为 HTML。

### 2. 流式输出（增量渲染）

对于流式输出，采用**行级增量渲染**策略：

1. **流式过程中**：显示原始文本
2. **行结束时**：检测到换行符 `\n` 时，渲染该行为 HTML
3. **流式结束后**：对完整文本做最终渲染

这种方式既保持了流式输出的流畅性，又能实时看到格式化效果。

## 性能优化

### 优化策略

1. **行级渲染**：只在行结束时触发渲染，避免过于频繁的重渲染
2. **智能检测**：自动检测 Markdown 语法，纯文本不进行渲染
3. **渐进式增强**：流式过程中先显示原始内容，最后再完整渲染

### 性能建议

- 对于长文本，渲染会在行结束时进行，避免阻塞 UI
- 用户消息不进行 Markdown 渲染（保持原始格式）
- 只对 AI 响应进行渲染

## 安装依赖

## 测试渲染功能

运行测试脚本：

```bash
.venv\Scripts\python test_markdown_render.py
```

测试脚本会验证：
- 基本 Markdown 渲染
- 代码块渲染
- 列表和表格渲染
- LaTeX 公式渲染
- 增量流式渲染

## 使用示例

### 在聊天中使用

AI 响应中可以直接使用 Markdown 和 LaTeX 语法：

```
# 计算结果

根据计算，我们得到以下结果：

- 总和: **150**
- 平均值: *25*

数学公式：
$$
S = \sum_{i=1}^{10} i^2 = 385
$$

代码示例：
```python
def calculate(n):
    return sum(range(n+1))
```
```

### 样式自定义

Markdown 渲染的样式在 `utils/markdown_renderer.py` 中的 `get_base_css()` 方法定义。

如需自定义样式（如颜色、字体等），可以修改该方法中的 CSS。

## 技术实现

### 核心组件

1. **MarkdownRenderer** ([`utils/markdown_renderer.py`](utils/markdown_renderer.py:1))
   - 核心渲染引擎
   - 支持增量渲染
   - LaTeX 公式支持

2. **ModernMessageBubble** ([`ui/chat_box.py`](ui/chat_box.py:746))
   - 消息气泡组件
   - 集成 Markdown 渲染
   - 支持流式更新

3. **流式处理** ([`ui/chat_box.py`](ui/chat_box.py:1848))
   - `handle_stream_chunk()`: 处理流式块
   - `append_text(render_html=True)`: 增量渲染
   - `finalize_rendering()`: 最终渲染

### 渲染流程

```
用户消息 → AI 处理 → 流式输出
                          ↓
                    检测行结束符
                          ↓
              ┌──────────┴──────────┐
              ↓                     ↓
         继续累积              触发渲染
         (原始文本)            (HTML)
              ↓                     ↓
              └──────────┬──────────┘
                         ↓
                    流式完成
                         ↓
                   最终完整渲染
```

## 常见问题

### Q: LaTeX 公式不显示？

A: 确保 `markdown-katex` 已安装：
```bash
pip install markdown-katex
```

### Q: 中文显示有问题？

A: 确保字体设置正确。在 CSS 中已配置：
```css
font-family: 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif;
```

### Q: 渲染性能慢？

A: 增量渲染会按行进行，对于特别长的文本，建议考虑分块输出。

### Q: 如何禁用 Markdown 渲染？

A: 在 `ModernMessageBubble` 中设置 `enable_markdown = False`。

## 贡献

如需改进渲染功能，可以修改：
- `utils/markdown_renderer.py` - 渲染逻辑
- `ui/chat_box.py` - UI 集成
