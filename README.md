# 全球人才需求扫描器 v1.0

自动扫描国内外主流招聘平台的岗位需求与招聘人数，每日生成多格式人才需求日报。

## 功能特性

- **多平台采集**：覆盖 Boss直聘、猎聘、智联招聘、拉勾（国内）+ LinkedIn、Indeed、Glassdoor（国际）
- **智能分析**：职位类别自动分类、技能标签提取、招聘人数估算、薪资分析
- **多格式报告**：HTML（可视化）、JSON（结构化）、CSV（Excel友好）
- **演示模式**：无需真实爬取即可生成模拟数据查看报告效果
- **每日自动化**：支持 Cron / Launchd 定时运行

## 项目结构

```
├── scanner.py              # 主入口
├── config.yaml             # 配置文件
├── run.sh                  # 一键启动脚本
├── scraper/                # 数据采集模块
│   ├── base.py             # 爬虫基类
│   ├── boss.py             # Boss直聘
│   ├── liepin.py           # 猎聘
│   ├── zhilian.py          # 智联招聘
│   ├── lagou.py            # 拉勾
│   ├── linkedin.py         # LinkedIn
│   ├── indeed.py           # Indeed
│   ├── glassdoor.py        # Glassdoor
│   ├── demo.py             # 演示数据生成
│   └── manager.py          # 爬虫管理器
├── processor/              # 数据处理模块
│   └── aggregator.py       # 数据聚合分析
├── reporter/               # 报告生成模块
│   ├── generator.py        # 多格式报告生成
│   └── templates/          # HTML模板
├── reports/                # 报告输出目录
├── data/                   # 数据缓存目录
└── logs/                   # 日志目录
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行

```bash
# 演示模式（生成模拟数据，立即查看报告效果）
python scanner.py --demo

# 或使用一键脚本
./run.sh --demo

# 真实采集模式（需要网络能访问目标平台）
python scanner.py
```

### 3. 查看报告

报告自动生成在 `reports/` 目录：
- `talent_report_YYYY-MM-DD.html` - 可视化HTML日报
- `talent_report_YYYY-MM-DD.json` - 结构化数据
- `talent_summary_YYYY-MM-DD.csv` - Excel兼容表格

## 命令行参数

| 参数 | 说明 |
|------|------|
| `--config, -c` | 配置文件路径（默认 config.yaml） |
| `--output, -o` | 报告输出目录 |
| `--date, -d` | 指定报告日期 YYYY-MM-DD |
| `--format, -f` | 报告格式: html/json/csv/all |
| `--demo` | 使用演示数据 |
| `--skip-scrape` | 跳过采集，用缓存生成 |
| `--platform, -p` | 指定平台（逗号分隔） |
| `--verbose, -v` | 详细日志输出 |

## 配置文件

编辑 `config.yaml` 自定义：
- 搜索关键词和城市
- 启用/禁用平台
- 报告格式和标题
- 职位类别映射

## 每日自动化

### macOS / Linux (cron)

```bash
# 每天早上9点自动运行
crontab -e
# 添加:
0 9 * * * cd /path/to/project && ./run.sh >> logs/cron.log 2>&1
```

### macOS (launchd)

创建 `~/Library/LaunchAgents/com.talent.scanner.plist` 实现更可靠的定时任务。

## 注意事项

1. **反爬限制**：多数招聘平台有反爬机制，真实采集可能被限制。工具已内置重试、延迟等策略
2. **演示模式**：当无法从真实平台采集数据时，自动降级为演示数据，确保报告功能完整可用
3. **招聘人数**：多数平台不直接显示招聘人数，工具通过公司规模、热招标签等信号进行估算
4. **合规使用**：请遵守目标网站的 robots.txt 和使用条款，仅用于个人分析
