# Morning Pulse - 每日订阅摘要生成器

自动抓取 RSS、YouTube、Bilibili 订阅源，通过 DeepSeek API 生成中文摘要，并以 Markdown 报告输出，支持自动打开报告（如 Typora）。

## 功能特性

- **RSS 源抓取**：支持任意标准 RSS 2.0 / Atom 订阅。
- **YouTube 频道**（开发中，尚未稳定）。
- **Bilibili UP 主**（请在 .env 文件中设置 BILIBILI_SESSDATA，详见配置说明）。
- **DeepSeek 摘要**：调用 DeepSeek Chat API 为每篇文章生成 100-300 字中文摘要。
- **状态记录**：自动记录已处理条目，避免重复摘要。
- **测试模式**：`--test` 参数强制全量获取，忽略已有状态，便于调试。
- **报告自动打开**：报告生成后自动用 Typora（或系统默认 Markdown 编辑器）打开。
- **忽略文件**：.gitignore 已配置忽略虚拟环境、缓存、输出、状态数据库等生成文件。

## 环境要求

- Python 3.8+
- 虚拟环境（推荐）venv
- DeepSeek API 密钥（免费注册 [platform.deepseek.com](https://platform.deepseek.com)）

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/yangpeng1985/morning-pulse.git
cd morning-pulse
```

### 2. 创建并激活虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate   # macOS / Linux
# 或 Windows: venv\Scripts\activate
```


### 3. 安装依赖

```bash
pip install -r requirements.txt
```

或使用项目提供的脚本：

```bash
sh install_deps.sh
```


### 4. 配置 DeepSeek API 密钥

将密钥设置为环境变量（推荐），或直接在 config.yaml 的 llm.api_key 字段填入：

```bash
export DEEPSEEK_API_KEY="sk-your-key-here"
```

### 5. （可选）安装 yt-dlp（仅当需要抓取 YouTube 时）

```bash
pip install yt-dlp
```

### 6. 运行

```bash
# 普通模式（仅获取新增条目）
python main.py

# 测试模式（忽略状态，每次重新获取所有条目并生成摘要）
python main.py --test

# 指定自定义配置文件
python main.py --config my_config.yaml

# 按来源类型过滤（可重复使用 --source-type，只抓取指定类型的源）
python main.py --source-type bilibili --test
python main.py --source-type rss
```

### 7. 查看报告

报告默认保存在 output/ 目录下，命名格式为 YYYY-MM-DD.md。
运行结束后会自动用 Typora 打开生成的报告（如已安装 Typora）。
如需修改打开方式，在 config.yaml 中取消注释并配置 post_command 字段。


## 配置文件说明

项目根目录下的 config.yaml 包含所有可配置项，主要结构如下：

```bash
logging_level: INFO
state_db_path: state.db
output_dir: output

llm:
  model: deepseek-chat
  max_tokens: 300
  temperature: 0.3
  # api_key 留空则从环境变量 DEEPSEEK_API_KEY 获取

sources:
  - type: rss
    name: "卡瓦邦噶！"
    url: "https://www.kawabangga.com/feed"
  #  - type: youtube        # 取消注释以启用 YouTube
  #    name: "TechLinked"
  #    url: "https://www.youtube.com/@TechLinked"
  #    max_results: 5
  #  - type: bilibili       # 取消注释以启用 Bilibili
  #    name: "科技袁人"
  #    uid: 1788474

report:
  format: markdown

# post_command: "open -a Typora {file}"   # 可选自动打开命令

```

字段说明


 字段             说明                                  默认值
 ────────────────────────────────────────────────────────────────────
 logging_level    日志级别（DEBUG/INFO/WARNING/ERROR）  INFO
 state_db_path    状态数据库路径（SQLite）              state.db
 output_dir       报告输出目录                                     output
 llm.model        DeepSeek 模型名                                  deepseek-chat
 llm.max_tokens   生成摘要最大 token 数                            300
 llm.temperature  生成随机性（0~1）                                0.3
 post_command     报告生成后执行的命令，{file} 会被替换为报告路径  默认使用 open -a Typora {file}



## 项目结构


morning-pulse/
├── config.yaml            # 配置文件
├── main.py                # 主入口
├── summarizer.py          # 摘要生成器（DeepSeek）
├── reporter.py            # 报告生成器
├── state.py               # SQLite 状态存储
├── utils.py               # 工具函数（日志、日期）
├── fetchers/              # 各平台抓取器
│   ├── base.py            # 数据模型 Item
│   ├── rss_fetcher.py
│   ├── youtube_fetcher.py
│   └── bilibili_fetcher.py
├── requirements.txt       # Python 依赖
├── install_deps.sh        # 安装脚本
└── .gitignore             # Git 忽略规则



## 许可证

MIT
