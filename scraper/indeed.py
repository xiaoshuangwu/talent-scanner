"""Indeed爬虫"""

from scraper.base import BaseScraper


class IndeedScraper(BaseScraper):
    """Indeed - 通过公开页面采集"""

    def __init__(self, config, global_cfg, logger):
        super().__init__("indeed", config, global_cfg, logger)
        self.base_url = config.get("base_url", "https://www.indeed.com")

    def search_jobs(self, keyword: str, location: str = None) -> list:
        """搜索Indeed职位"""
        jobs = []

        try:
            url = f"{self.base_url}/jobs"
            params = {
                "q": keyword,
                "l": location or "",
                "fromage": "1",  # 最近1天
            }

            resp = self._safe_request(url, params=params)
            if resp:
                jobs = self._parse_search_results(resp.text, keyword, location)

        except Exception as e:
            self.logger.error(f"[Indeed] 采集异常: {e}")

        return jobs[:100]

    def _parse_search_results(self, html: str, keyword: str, location: str) -> list:
        """解析Indeed搜索结果"""
        jobs = []
        soup = self._parse_html(html)

        cards = soup.select(".job_seen_beacon, .cardOutline, .resultContent, [data-testid='job-card']")

        for card in cards:
            try:
                title_el = (
                    card.select_one(".jobTitle, h2.jobTitle, a[data-jk], h2 a") or
                    card.select_one("[data-testid='jobTitle']")
                )
                company_el = (
                    card.select_one(".companyName, [data-testid='company-name']") or
                    card.select_one("[class*='company']")
                )
                location_el = (
                    card.select_one(".companyLocation, [data-testid='text-location']") or
                    card.select_one("[class*='location']")
                )
                salary_el = (
                    card.select_one(".salary-snippet-container, .salaryOnly, [data-testid='salary-snippet']") or
                    card.select_one("[class*='salary']")
                )

                if title_el:
                    title_text = title_el.get_text(strip=True)
                    headcount = self._estimate_headcount(card.get_text())

                    job = {
                        "title": title_text,
                        "company": company_el.get_text(strip=True) if company_el else "",
                        "location": location_el.get_text(strip=True) if location_el else (location or ""),
                        "salary": salary_el.get_text(strip=True) if salary_el else "",
                        "requirements": self._extract_requirements(card),
                        "headcount": headcount,
                        "posted_date": self._extract_date(card),
                        "url": self._extract_url(card, title_el),
                        "skills": [],
                    }
                    jobs.append(self._normalize_job(job, "international", keyword))
            except Exception as e:
                self.logger.debug(f"[Indeed] 解析单条异常: {e}")
                continue

        return jobs

    def _estimate_headcount(self, text: str) -> int:
        """估算招聘人数"""
        text_lower = text.lower()
        if "urgently hiring" in text_lower or "multiple" in text_lower:
            return 4
        if "hiring immediately" in text_lower:
            return 3
        return 2

    def _extract_requirements(self, card) -> list:
        """提取要求"""
        snippet = card.select_one(".job-snippet, .underShelfFooter")
        if snippet:
            return [s.strip() for s in snippet.get_text("|").split("|") if s.strip()][:5]
        return []

    def _extract_date(self, card) -> str:
        """提取日期"""
        date_el = card.select_one(".date, .job-age, [class*='date'], [class*='posted']")
        return date_el.get_text(strip=True) if date_el else ""

    def _extract_url(self, card, title_el) -> str:
        """提取URL"""
        link = title_el.find("a") if title_el.name != "a" else title_el
        if link and link.get("href"):
            href = link["href"]
            if href.startswith("http"):
                return href
            elif href.startswith("/"):
                return f"{self.base_url}{href}"
            # Indeed特有的jk参数
            jk = link.get("data-jk", "")
            if jk:
                return f"{self.base_url}/viewjob?jk={jk}"
        return ""
