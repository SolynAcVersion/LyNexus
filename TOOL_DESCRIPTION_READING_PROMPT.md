# 工具描述阅读要求 Prompt 添加总结

## 目标
添加框架级硬编码 prompt，强制 AI 在使用工具前仔细阅读工具描述，特别是标记为 'CRITICAL' 或 'MUST' 的部分。

## 问题背景
用户报告 AI 在执行文件操作时没有遵循工具描述中 documented 的工作流程，例如：
- 工具 `ls` 的描述中明确说明要先调用 `get_system_info()` 获取系统路径
- AI 却没有执行这个 prerequisite 步骤

## 解决方案

### 新增方法
在 [aiclass.py:694-739](aiclass.py#L694-L739) 添加了 `_get_tool_description_reading_prompt()` 方法：

```python
def _get_tool_description_reading_prompt(self) -> str:
    """
    获取硬编码的工具描述阅读要求提示词
    这个提示词始终会被添加到系统提示中（当有工具启用时），确保 AI 仔细阅读工具描述
    这是框架级逻辑，不涉及用户自定义内容
    """
    return """【CRITICAL: Tool Description Reading Requirements - MANDATORY】

**MUST READ COMPLETE DESCRIPTIONS:**
You MUST carefully read the ENTIRE description for EACH tool before using it.

**PAY SPECIAL ATTENTION TO:**
Sections marked with:
- 'CRITICAL' or '**CRITICAL**'
- 'MUST' or '**MUST**'
- 'REQUIREMENT' or '**REQUIREMENT**'
- 'WORKFLOW' or '**WORKFLOW**'
- 'PREREQUISITE' or '**PREREQUISITE**'

...
"""
```

### Prompt 流更新
在 [aiclass.py:860](aiclass.py#L860) 的 `get_effective_system_prompt()` 方法中更新了 prompt 组装顺序：

**之前的顺序:**
```
工具描述 + 用户 system_prompt + Markdown 格式规范
```

**新的顺序:**
```
工具描述 + 框架级工具描述阅读要求 + 用户 system_prompt + Markdown 格式规范
```

具体代码：
```python
final_prompt = (
    desc + "\n\n" +
    self._get_tool_description_reading_prompt() + "\n\n" +
    base_prompt + "\n\n" +
    self._get_markdown_format_prompt()
)
```

## 设计原则

### ✅ 硬编码此 Prompt 的原因
这是**框架级逻辑**，不是用户自定义内容：
1. 强调阅读工具描述是系统的核心使用方式
2. 不涉及具体的工具名称（完全 generic）
3. 不涉及用户可配置的参数或格式
4. 类似于 Markdown 格式规范，属于框架必须强制执行的行为

### ✅ 避免硬编码工具名称
Prompt 中**完全没有**提到具体工具名如 'ls', 'cat', 'mkdir' 等：
- 只使用 generic 术语 "tool"
- 强调阅读工具描述中的标记
- 适用于任何 MCP 工具

### ✅ 位置和时机
- **位置**: 在工具描述之后、用户 system_prompt 之前
- **时机**: 当有工具启用时才会添加（line 860）
- **原因**: 让 AI 在看到用户自己的 prompt 之前先了解工具使用的基本要求

## Prompt 内容要点

1. **强制性要求**: "MUST read complete descriptions"
2. **关键标记识别**: 列出所有可能的重要标记（CRITICAL, MUST, REQUIREMENT, WORKFLOW, PREREQUISITE）
3. **解释原因**: 说明这些部分包含什么关键信息（prerequisites, dependencies, workflows）
4. **具体示例**: 提到有些操作需要先调用其他工具（但不指定具体工具名）
5. **实践步骤**: 5条明确的实践步骤
6. **后果说明**: 不遵循会导致操作失败

## 验证

✅ 框架级 prompt 已添加
✅ 完全 generic，不包含具体工具名
✅ 只在有工具启用时添加
✅ 位置合理（工具描述之后，用户 prompt 之前）
✅ 与现有的 Markdown 格式 prompt 类似，都是框架级硬编码

## 预期效果

AI 在使用工具时应该：
1. 仔细阅读每个工具的完整描述
2. 特别关注 'CRITICAL'、'MUST' 等标记的部分
3. 按照描述中的工作流程执行（如先调用 get_system_info）
4. 遵循工具描述中的 prerequisite 步骤

例如对于 `ls` 工具：
- AI 会看到描述中的 "**CRITICAL REQUIREMENT**: Call get_system_info() FIRST"
- AI 会遵循这个要求，先调用 get_system_info，再调用 ls
