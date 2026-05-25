"""Boss直聘爬虫"""

import re
import json
from scraper.base import BaseScraper


class BossScraper(BaseScraper):
    """Boss直聘 - 通过API或页面解析采集"""

    def __init__(self, config, global_cfg, logger):
        super().__init__("boss_zhipin", config, global_cfg, logger)
        self.api_url = config.get("api_endpoint",
            "https://www.zhipin.com/wapi/zpgeek/search/joblist.json")

    def search_jobs(self, keyword: str, location: str = None) -> list:
        """搜索Boss直聘职位"""
        jobs = []

        try:
            params = {
                "query": keyword,
                "page": 1,
                "pageSize": 30,
            }
            if location:
                # Boss直聘需要城市编码，这里做简单映射
                city_map = {
                    "北京": "101010100", "上海": "101020100", "深圳": "101280600",
                    "杭州": "101210100", "广州": "101280100", "成都": "101270100",
                }
                params["city"] = city_map.get(location, "101010100")

            resp = self._safe_request(
                self.api_url,
                params=params,
                headers={"Referer": "https://www.zhipin.com/"}
            )

            if resp and resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    job_list = data.get("zpData", {}).get("jobList", [])
                    for item in job_list:
                        job = self._parse_boss_job(item, keyword, location)
                        jobs.append(self._normalize_job(job, "domestic", keyword))

            # 限制每关键词最多采集100条
            if len(jobs) > 100:
                jobs = jobs[:100]

        except Exception as e:
            self.logger.error(f"[Boss直聘] API请求异常: {e}")
            # 降级方案：使用搜索结果页面进行解析
            jobs = self._fallback_search(keyword, location)

        return jobs

    def _parse_boss_job(self, item: dict, keyword: str, location: str) -> dict:
        """解析Boss直聘API返回的单条职位"""
        return {
            "title": item.get("jobName", ""),
            "company": item.get("brandName", ""),
            "location": item.get("cityName", location or ""),
            "salary": item.get("salaryDesc", ""),
            "requirements": self._parse_requirements(item.get("skills", [])),
            "headcount": self._estimate_headcount(item),
            "posted_date": item.get("lastModifyTime", ""),
            "url": f"https://www.zhipin.com/job_detail/{item.get('encryptJobId', '')}.html",
            "skills": item.get("skills", [])[:10] if isinstance(item.get("skills"), list) else [],
        }

    def _parse_requirements(self, skills: list) -> list:
        """提取技能要求"""
        if not skills:
            return []
        if isinstance(skills, list):
            return [s.get("name", str(s)) if isinstance(s, dict) else str(s) for s in skills[:10]]
        return []

    def _estimate_headcount(self, item: dict) -> int:
        """
        估算招聘人数
        Boss直聘不直接显示招聘人数，通过以下信号估算：
        - 公司规模越大，招聘人数越多
        - 招聘信息活跃度
        - 默认保守估计：1-3人
        """
        company_size = item.get("brandSizeName", "")
        if "10000人以上" in company_size:
            return 3
        elif "1000-9999人" in company_size:
            return 2
        return 1

    def _fallback_search(self, keyword: str, location: str) -> list:
        """降级方案：通过页面解析"""
        jobs = []
        try:
            url = f"https://www.zhipin.com/web/geek/job?query={keyword}"
            if location:
                url += f"&city={location}"
            resp = self._safe_request(url)
            if resp:
                soup = self._parse_html(resp.text)
                cards = soup.select(".job-card-wrapper")
                for card in cards[:30]:
                    title_el = card.select_one(".job-name")
                    company_el = card.select_one(".company-name")
                    salary_el = card.select_one(".salary")
                    if title_el:
                        job = {
                            "title": title_el.get_text(strip=True),
                            "company": company_el.get_text(strip=True) if company_el else "",
                            "location": location or "",
                            "salary": salary_el.get_text(strip=True) if salary_el else "",
                            "requirements": [],
                            "headcount": 1,
                            "posted_date": "",
                            "url": "",
                            "skills": [],
                        }
                        jobs.append(self._normalize_job(job, "domestic", keyword))
        except Exception as e:
            self.logger.error(f"[Boss直聘] 降级采集失败: {e}")
        return jobs
