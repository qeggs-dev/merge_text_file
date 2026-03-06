# Merge Text File

这是一个用于合并文本文件的Python工具，
适合将项目中的多个文本文件（如代码文件、文档等）合并成一个单一的输出文件。
工具支持通过模板（Jinja2）自定义合并方式，并提供了文件包含和格式化选项。

## 功能特点

- 📁 **递归合并**：自动遍历目录，合并所有文本文件
- 🎨 **自定义包装**：提供多种文件内容包装方式（默认标记、Markdown代码块、自定义模板）
- 📝 **模板支持**：使用Jinja2模板语言，可动态生成合并结果
- 🎯 **文件过滤**：支持正则表达式模式匹配，只合并特定文件
- 📊 **日志记录**：日志输出，便于调试和追踪

## 快速启动

```bash
git clone https://github.com/qeggs-dev/Sloves_Starter.git
copy Sloves_Starter/Sloves_Starter.py ./run.py
python run.py
```

## 配置文件

工具需要 `guidance.json` 或 `guidance.yml` 配置文件：

### JSON格式 (guidance.json)
```json
{
    "index_file": "index.md",
    "encoding": "utf-8",
    "output_file": "output.md"
}
```

### YAML格式 (guidance.yml)
```yaml
index_file: "index.md"
encoding: "utf-8"
output_file: "output.md"
```

### 配置参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `index_file` | 入口模板文件路径 | "index.md" |
| `encoding` | 文件编码 | "utf-8" |
| `output_file` | 输出文件路径 | "output.md" |

## 使用方法

### 基本用法

1. 创建配置文件
2. 创建入口模板文件（如 `index.md`）
3. 运行工具：

```bash
python merge_text_file.py
```
or
```bash
python run.py
```

### 模板语法

在入口模板文件中，可以使用以下函数：

#### `merge_text(path, encoding=None, file_path_pattern=None, wrap_file=None)`
合并指定路径下的所有文件

```jinja2
{% set content = merge_text("./src") -%}
{{ content }}
```

#### `tree(path)`

生成指定路径下的文件树

```jinja2
{{ tree("./src") }}
```

#### `wrap_file(text, file_path)`
默认的文件包装方式，生成如下格式：
```
[file: "./path/to/file.txt"]
[file content begin]
文件内容...
[file content end]
```

#### `get_markdown_code_block_wrap(code_type)`
获取Markdown代码块包装器

```jinja2
{% set content = merge_text("./src", wrap_file=get_markdown_code_block_wrap("python")) -%}
{{ content }}
```

生成：
``` python
print("Hello World")
```

#### `get_custom_wrap(template)`
获取自定义模板包装器

```jinja2
{% set my_wrap = get_custom_wrap("File: {{ file_path }}\n---\n{{ text }}") -%}
{% set content = merge_text("./docs", wrap_file=my_wrap) -%}
{{ content }}
```

### 完整示例

**index.md**:
```jinja2
# 项目文档

生成时间：{{ now.strftime("%Y-%m-%d %H:%M:%S") }}

## 源代码

{% set python_wrap = get_markdown_code_block_wrap("python") -%}
{% set source_code = merge_text("./src", file_path_pattern=".*\\.py$", wrap_file=python_wrap) -%}
{{ source_code }}

## 配置文件

{% set config_wrap = get_custom_wrap("=== {{ file_path }} ===\n{{ text }}\n===") -%}
{% set configs = merge_text(".", file_path_pattern=".*\\.(json|yml)$", wrap_file=config_wrap) -%}
{{ configs }}
```

## 日志

日志输出到：
- 控制台（实时）
- `./logs/merge_text_file_时间戳.log`（文件）

## 注意事项

1. 路径处理：所有路径都相对于 `index_file` 所在的目录
2. 文件编码：确保所有文件使用相同的编码（默认为UTF-8）
3. 正则表达式：`file_path_pattern` 使用Python正则表达式语法
4. 错误处理：读取失败的文件会显示错误信息，不会中断程序

## 许可证

[MIT License](LICENSE)