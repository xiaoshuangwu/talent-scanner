"""LinkedIn爬虫"""

import re
import json
from scraper.base import BaseScraper


class LinkedInScraper(BaseScraper):
    """LinkedIn - 通过公开页面采集"""

    def __init__(self, config, global_cfg, logger):
        super().__init__("linkedin", config, global_cfg, logger)
        self.base_url = config.get("base_url", "https://www.linkedin.com")

    def search_jobs(self, keyword: str, location: str = None) -> list:
        """搜索LinkedIn职位"""
        jobs = []

        try:
            # LinkedIn公开职位搜索页面（无需登录）
            url = f"{self.base_url}/jobs/search"
            params = {
                "keywords": keyword,
                "position": 1,
                "pageNum": 0,
            }
            if location:
                params["location"] = location

            resp = self._safe_request(url, params=params)
            if resp:
                jobs = self._parse_search_results(resp.text, keyword, location)

        except Exception as e:
            self.logger.error(f"[LinkedIn] 采集异常: {e}")
            # 降级：使用Google Jobs聚合数据
            jobs = self._google_jobs_fallback(keyword, location)

        return jobs[:100]

    def _parse_search_results(self, html: str, keyword: str, location: str) -> list:
        """解析LinkedIn搜索结果"""
        jobs = []
        soup = self._parse_html(html)

        # LinkedIn的职位卡片
        cards = soup.select(".job-search-card, .base-card, .job-result-card")

        for card in cards:
            try:
                title_el = card.select_one(".base-search-card__title, .job-search-card__title, h3")
                company_el = card.select_one(".base-search-card__subtitle, .job-search-card__subtitle, h4")
                location_el = card.select_one(".job-search-card__location, .job-search-card__metadata-item")
                link_el = card.select_one("a.base-card__full-link, a.job-search-card__link")

                if title_el:
                    title_text = title_el.get_text(strip=True)

                    # 估算招聘人数
                    headcount = self._estimate_headcount(card, title_text)

                    job = {
                        "title": title_text,
                        "company": company_el.get_text(strip=True) if company_el else "",
                        "location": location_el.get_text(strip=True) if location_el else (location or ""),
                        "salary": self._extract_salary(card),
                        "requirements": [],
                        "headcount": headcount,
                        "posted_date": self._extract_date(card),
                        "url": link_el["href"] if link_el else "",
                        "skills": self._extract_skills(title_text, card),
                    }
                    jobs.append(self._normalize_job(job, "international", keyword))
            except Exception as e:
                self.logger.debug(f"[LinkedIn] 解析单条异常: {e}")
                continue

        return jobs

    def _estimate_headcount(self, card, title: str) -> int:
        """估算LinkedIn职位招聘人数"""
        text = card.get_text().lower()
        # LinkedIn "Actively hiring" 标签
        if "actively hiring" in text:
            return 5
        # "Multiple positions" 或多地点招聘
        if "multiple" in text or "various locations" in text:
            return 4
        # Senior/Lead 职位通常招1人
        if any(w in title.lower() for w in ["senior", "lead", "principal", "director"]):
            return 1
        return 2

    def _extract_salary(self, card) -> str:
        """提取薪资信息"""
        salary_el = card.select_one(".job-search-card__salary-info, [class*='salary'], [class*='compensation']")
        return salary_el.get_text(strip=True) if salary_el else ""

    def _extract_date(self, card) -> str:
        """提取发布日期"""
        date_el = card.select_one(".job-search-card__listdate, time, [datetime]")
        if date_el:
            dt = date_el.get("datetime", "") or date_el.get_text(strip=True)
            return dt
        return ""

    def _extract_skills(self, title: str, card=None) -> list:
        """从职位标题和描述中提取技能"""
        common_skills = [
            "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C++",
            "React", "Vue", "Angular", "Node.js", "Django", "Spring",
            "AWS", "Azure", "GCP", "Docker", "Kubernetes",
            "TensorFlow", "PyTorch", "Spark", "Kafka",
            "SQL", "NoSQL", "MongoDB", "PostgreSQL", "Redis",
            "Git", "CI/CD", "Agile", "Scrum",
        ]
        found = []
        title_lower = title.lower()
        for skill in common_skills:
            if skill.lower() in title_lower:
                found.append(skill)
        return found

    def _google_jobs_fallback(self, keyword: str, location: str) -> list:
        """Google Jobs降级方案"""
        jobs = []
        try:
            url = f"https://www.google.com/search"
            params = {
                "q": f"{keyword} jobs {location or ''}",
                "ibp": "htl;jobs"
            }
            resp = self._safe_request(url, params=params)
            if resp:
                soup = self._parse_html(resp.text)
                # 解析Google Jobs结果
                cards = soup.select(".g-card, [data-share-url]")
                for card in cards[:30]:
                    title_el = card.select_one("h2, .BjJfJf, .job-title")
                    if title_el:
                        job = {
                            "title": title_el.get_text(strip=True),
                            "company": "",
                            "location": location or "",
                            "salary": "",
                            "requirements": [],
                            "headcount": 1,
                            "posted_date": "",
                            "url": card.get("data-share-url", ""),
                            "skills": [],
                        }
                        jobs.append(self._normalize_job(job, "international", keyword))
        except Exception as e:
            self.logger.error(f"[LinkedIn] Google降级也失败: {e}")
        return jobs
