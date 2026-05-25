"""猎聘爬虫"""

import re
import json
from scraper.base import BaseScraper


class LiepinScraper(BaseScraper):
    """猎聘 - 页面解析方式采集"""

    def __init__(self, config, global_cfg, logger):
        super().__init__("liepin", config, global_cfg, logger)
        self.base_url = config.get("base_url", "https://www.liepin.com")

    def search_jobs(self, keyword: str, location: str = None) -> list:
        """搜索猎聘职位"""
        jobs = []

        try:
            # 猎聘搜索URL
            url = f"{self.base_url}/zhaopin/"
            params = {"key": keyword}
            if location:
                params["dqs"] = self._city_code(location)

            resp = self._safe_request(url, params=params)
            if resp:
                jobs = self._parse_search_results(resp.text, keyword, location)

        except Exception as e:
            self.logger.error(f"[猎聘] 采集异常: {e}")

        return jobs[:100]

    def _parse_search_results(self, html: str, keyword: str, location: str) -> list:
        """解析搜索结果页面"""
        jobs = []
        soup = self._parse_html(html)

        # 猎聘的职位卡片选择器
        cards = soup.select(".job-list-item, .job-card, .job-info")

        for card in cards:
            try:
                title_el = (
                    card.select_one(".job-title") or
                    card.select_one(".job-name") or
                    card.select_one("h3")
                )
                company_el = (
                    card.select_one(".company-name") or
                    card.select_one(".company") or
                    card.select_one("[class*='company']")
                )
                salary_el = (
                    card.select_one(".job-salary") or
                    card.select_one(".salary") or
                    card.select_one("[class*='salary']")
                )
                req_el = card.select_one(".job-labels, .tag-list, .requirement")

                if title_el:
                    title_text = title_el.get_text(strip=True)
                    # 提取技能标签
                    skills = []
                    if req_el:
                        labels = req_el.select("span, .label, .tag")
                        skills = [l.get_text(strip=True) for l in labels if l.get_text(strip=True)]

                    # 估算招聘人数（猎聘有时会显示）
                    headcount = self._extract_headcount(card)

                    job = {
                        "title": title_text,
                        "company": company_el.get_text(strip=True) if company_el else "",
                        "location": location or self._extract_location(card),
                        "salary": salary_el.get_text(strip=True) if salary_el else "",
                        "requirements": skills,
                        "headcount": headcount,
                        "posted_date": self._extract_date(card),
                        "url": self._extract_url(card, title_el),
                        "skills": skills,
                    }
                    jobs.append(self._normalize_job(job, "domestic", keyword))
            except Exception as e:
                self.logger.debug(f"[猎聘] 解析单条异常: {e}")
                continue

        return jobs

    def _extract_headcount(self, card) -> int:
        """提取或估算招聘人数"""
        # 猎聘部分职位会显示"招X人"
        text = card.get_text()
        match = re.search(r'招\s*(\d+)\s*人', text)
        if match:
            return int(match.group(1))
        # 猎聘"急聘"标签通常意味着多个名额
        if "急聘" in text:
            return 3
        return 1

    def _extract_location(self, card) -> str:
        """提取工作地点"""
        loc_el = card.select_one(".job-location, .location, .area, [class*='location']")
        return loc_el.get_text(strip=True) if loc_el else ""

    def _extract_date(self, card) -> str:
        """提取发布日期"""
        date_el = card.select_one(".time, .date, .publish-time, [class*='time']")
        return date_el.get_text(strip=True) if date_el else ""

    def _extract_url(self, card, title_el) -> str:
        """提取职位链接"""
        link = title_el.find("a") if title_el.name != "a" else title_el
        if link and link.get("href"):
            href = link["href"]
            return href if href.startswith("http") else f"{self.base_url}{href}"
        return ""

    def _city_code(self, city: str) -> str:
        """城市编码映射"""
        codes = {
            "北京": "010", "上海": "020", "深圳": "050090",
            "杭州": "080020", "广州": "050020", "成都": "280020",
        }
        return codes.get(city, "010")
