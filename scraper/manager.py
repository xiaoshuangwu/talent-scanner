"""爬虫管理器 - 调度所有平台爬虫"""

from scraper.boss import BossScraper
from scraper.liepin import LiepinScraper
from scraper.zhilian import ZhilianScraper
from scraper.lagou import LagouScraper
from scraper.linkedin import LinkedInScraper
from scraper.indeed import IndeedScraper
from scraper.glassdoor import GlassdoorScraper
from scraper.demo import DemoDataGenerator


# 平台爬虫注册表
SCRAPER_REGISTRY = {
    "boss_zhipin": BossScraper,
    "liepin": LiepinScraper,
    "zhilian": ZhilianScraper,
    "lagou": LagouScraper,
    "linkedin": LinkedInScraper,
    "indeed": IndeedScraper,
    "glassdoor": GlassdoorScraper,
}


class ScraperManager:
    """爬虫管理器：负责创建平台爬虫实例并统一调度采集"""

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    def scrape_all(self, platform_filter: list = None) -> list:
        """
        调度所有启用的平台爬虫执行采集

        Args:
            platform_filter: 可选，仅采集指定平台列表

        Returns:
            list: 所有采集到的岗位数据
        """
        all_jobs = []
        platforms = self.config.all_platforms

        # 检测是否有实际数据（如果所有爬虫都采集不到数据，则使用演示数据）
        real_data_collected = False

        for p in platforms:
            name = p["name"]
            # 如果指定了平台过滤，跳过不匹配的
            if platform_filter and name not in platform_filter:
                continue

            scraper_cls = SCRAPER_REGISTRY.get(name)
            if not scraper_cls:
                self.logger.warning(f"平台 '{name}' 未注册爬虫，跳过")
                continue

            try:
                self.logger.info(f"📡 开始采集 [{name}] ({p['region']})")
                scraper = scraper_cls(p["config"], self.config, self.logger)
                jobs = scraper.scrape()
                if jobs:
                    real_data_collected = True
                self.logger.info(f"📡 [{name}] 采集完成: {len(jobs)} 条")
                all_jobs.extend(jobs)
            except Exception as e:
                self.logger.error(f"❌ [{name}] 采集失败: {e}")

        # 如果没有采集到任何真实数据，使用演示数据
        if not real_data_collected and not platform_filter:
            self.logger.warning("⚠️ 所有平台均未采集到数据（可能因反爬限制），将使用演示数据生成报告")
            demo = DemoDataGenerator(self.logger)
            all_jobs = demo.generate(count=300)

        return all_jobs
