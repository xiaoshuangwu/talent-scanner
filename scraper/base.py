"""爬虫基类"""

import time
import random
import requests
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup


class BaseScraper(ABC):
    """所有平台爬虫的基类"""

    def __init__(self, platform_name: str, platform_config: dict, global_config, logger):
        self.name = platform_name
        self.cfg = platform_config
        self.global_cfg = global_config
        self.logger = logger
        self.session = self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            "User-Agent": self.global_cfg.get("global.user_agent",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) TalentScanner/1.0"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        })
        return session

    def _delay(self):
        """请求延迟，避免反爬"""
        base_delay = self.global_cfg.get("global.request_delay", 2)
        jitter = random.uniform(0.5, 1.5)
        time.sleep(base_delay * jitter)

    def _safe_request(self, url: str, method="GET", **kwargs) -> requests.Response:
        """带重试的请求"""
        retries = self.global_cfg.get("global.max_retries", 3)
        timeout = self.global_cfg.get("global.timeout", 30)

        for attempt in range(retries):
            try:
                self._delay()
                if method == "GET":
                    resp = self.session.get(url, timeout=timeout, **kwargs)
                else:
                    resp = self.session.post(url, timeout=timeout, **kwargs)
                resp.raise_for_status()
                return resp
            except requests.RequestException as e:
                self.logger.warning(f"[{self.name}] 请求失败 (尝试 {attempt + 1}/{retries}): {e}")
                if attempt == retries - 1:
                    raise
                time.sleep(2 ** attempt)  # 指数退避
        return None

    def _parse_html(self, html: str) -> BeautifulSoup:
        """解析HTML"""
        return BeautifulSoup(html, "lxml")

    @abstractmethod
    def search_jobs(self, keyword: str, location: str = None) -> list:
        """
        搜索职位

        Returns:
            list: 职位列表，每个职位为dict格式:
                {
                    "title": str,
                    "company": str,
                    "location": str,
                    "salary": str,
                    "requirements": list,
                    "headcount": int,  # 招聘人数（估计值）
                    "posted_date": str,
                    "platform": str,
                    "region": str,
                    "url": str,
                    "category": str,
                    "skills": list,
                }
        """
        pass

    def scrape(self) -> list:
        """执行采集：遍历所有关键词和城市"""
        all_jobs = []
        keywords = self.cfg.get("search_keywords", [])
        locations = self.cfg.get("cities", self.cfg.get("locations", [None]))

        for keyword in keywords:
            self.logger.info(f"[{self.name}] 搜索关键词: '{keyword}'")
            for loc in locations:
                try:
                    jobs = self.search_jobs(keyword, loc)
                    all_jobs.extend(jobs)
                    self.logger.debug(f"[{self.name}] '{keyword}' @ {loc}: {len(jobs)} 条")
                except Exception as e:
                    self.logger.error(f"[{self.name}] 采集失败 keyword='{keyword}' location='{loc}': {e}")
        return all_jobs

    def _normalize_job(self, raw: dict, region: str, keyword: str) -> dict:
        """标准化职位数据格式"""
        return {
            "title": raw.get("title", "").strip(),
            "company": raw.get("company", "").strip(),
            "location": raw.get("location", "").strip(),
            "salary": raw.get("salary", ""),
            "requirements": raw.get("requirements", []),
            "headcount": raw.get("headcount", 1),
            "posted_date": raw.get("posted_date", ""),
            "platform": self.name,
            "region": region,
            "url": raw.get("url", ""),
            "category": self._categorize(raw.get("title", ""), keyword),
            "skills": raw.get("skills", []),
            "search_keyword": keyword,
        }

    @staticmethod
    def _categorize(title: str, keyword: str) -> str:
        """根据职位名称和搜索关键词推断分类"""
        title_lower = title.lower()
        kw_lower = keyword.lower()

        if any(w in title_lower + kw_lower for w in ["ai", "机器学习", "深度学习", "算法", "nlp", "数据科学", "数据工程"]):
            return "AI与数据"
        elif any(w in title_lower + kw_lower for w in ["前端", "后端", "全栈", "移动", "react", "vue", "angular", "flutter"]):
            return "Web与移动"
        elif any(w in title_lower + kw_lower for w in ["devops", "运维", "sre", "云", "kubernetes", "docker", "ci/cd"]):
            return "云计算与DevOps"
        elif any(w in title_lower + kw_lower for w in ["产品", "project", "scrum", "管理"]):
            return "产品与管理"
        elif any(w in title_lower + kw_lower for w in ["安全", "security", "渗透"]):
            return "安全"
        elif any(w in title_lower + kw_lower for w in ["测试", "qa", "quality"]):
            return "测试与质量"
        return "其他"
