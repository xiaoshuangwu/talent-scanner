# 人才需求扫描器 - 主入口

import sys
import os
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config import Config
from utils.logger import setup_logger
from scraper.manager import ScraperManager
from processor.aggregator import DataAggregator
from reporter.generator import ReportGenerator


def main():
    parser = argparse.ArgumentParser(description="全球人才需求扫描与日报生成工具")
    parser.add_argument("--config", "-c", default="config.yaml", help="配置文件路径")
    parser.add_argument("--output", "-o", default=None, help="报告输出目录（覆盖配置文件）")
    parser.add_argument("--date", "-d", default=None, help="指定报告日期 YYYY-MM-DD（默认今天）")
    parser.add_argument("--format", "-f", choices=["html", "json", "csv", "all"], default=None,
                        help="报告输出格式")
    parser.add_argument("--skip-scrape", action="store_true", help="跳过采集，仅用缓存数据生成报告")
    parser.add_argument("--platform", "-p", default=None, help="仅采集指定平台（多个用逗号分隔）")
    parser.add_argument("--demo", action="store_true", help="强制使用演示数据生成（跳过真实采集）")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")

    args = parser.parse_args()

    # 初始化
    config = Config(args.config)
    logger = setup_logger(config, args.verbose)
    logger.info("=" * 60)
    logger.info("  全球人才需求扫描器 v1.0")
    logger.info(f"  启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # 覆盖配置
    if args.output:
        config.set("global.output_dir", args.output)
    if args.format:
        config.set("report.formats", [args.format])

    report_date = args.date or datetime.now().strftime("%Y-%m-%d")

    # 确保输出目录存在
    os.makedirs(config.get("global.output_dir"), exist_ok=True)
    os.makedirs(config.get("global.data_dir"), exist_ok=True)
    os.makedirs(config.get("global.log_dir"), exist_ok=True)

    # Step 1: 采集数据
    all_jobs = []
    if not args.skip_scrape:
        logger.info("🚀 开始采集招聘数据...")

        if args.demo:
            # 强制演示模式
            from scraper.demo import DemoDataGenerator
            demo = DemoDataGenerator(logger)
            all_jobs = demo.generate(count=300)
        else:
            manager = ScraperManager(config, logger)
            all_jobs = manager.scrape_all(
                platform_filter=args.platform.split(",") if args.platform else None
            )
        logger.info(f"✅ 采集完成，共获取 {len(all_jobs)} 条岗位数据")

        # 保存原始数据
        import json
        raw_path = os.path.join(config.get("global.data_dir"), f"raw_{report_date}.json")
        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump(all_jobs, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 原始数据已保存: {raw_path}")
    else:
        # 从缓存加载
        import json
        raw_path = os.path.join(config.get("global.data_dir"), f"raw_{report_date}.json")
        if os.path.exists(raw_path):
            with open(raw_path, "r", encoding="utf-8") as f:
                all_jobs = json.load(f)
            logger.info(f"📂 从缓存加载 {len(all_jobs)} 条岗位数据")
        else:
            logger.error(f"缓存文件不存在: {raw_path}")
            sys.exit(1)

    # Step 2: 数据处理与聚合
    logger.info("📊 开始数据处理与聚合...")
    aggregator = DataAggregator(config)
    report_data = aggregator.aggregate(all_jobs, report_date)
    logger.info("✅ 数据处理完成")

    # Step 3: 生成报告
    logger.info("📝 开始生成报告...")
    generator = ReportGenerator(config)
    reports = generator.generate(report_data, report_date)
    for fmt, path in reports.items():
        logger.info(f"✅ {fmt.upper()} 报告已生成: {path}")

    logger.info("=" * 60)
    logger.info(f"  🎉 任务完成！共生成 {len(reports)} 份报告")
    logger.info(f"  报告日期: {report_date}")
    logger.info(f"  输出目录: {config.get('global.output_dir')}")
    logger.info("=" * 60)

    return reports


if __name__ == "__main__":
    main()
