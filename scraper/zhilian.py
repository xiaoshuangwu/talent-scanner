"""智联招聘爬虫"""

from scraper.base import BaseScraper


class ZhilianScraper(BaseScraper):
    """智联招聘 - 页面解析采集"""

    def __init__(self, config, global_cfg, logger):
        super().__init__("zhilian", config, global_cfg, logger)
        self.base_url = config.get("base_url", "https://www.zhaopin.com")

    def search_jobs(self, keyword: str, location: str = None) -> list:
        jobs = []
        try:
            url = f"{self.base_url}/sou/"
            params = {"kw": keyword}
            if location:
                params["jl"] = location

            resp = self._safe_request(url, params=params)
            if resp:
                soup = self._parse_html(resp.text)
                cards = soup.select(".joblist-box__item, .job-card, .positionlist-item")

                for card in cards:
                    try:
                        title_el = card.select_one(".job-title, .positionlist__name, h3 a")
                        company_el = card.select_one(".company-title, .company__name")
                        salary_el = card.select_one(".job-salary, .red, [class*='salary']")

                        if title_el:
                            job = {
                                "title": title_el.get_text(strip=True),
                                "company": company_el.get_text(strip=True) if company_el else "",
                                "location": location or "",
                                "salary": salary_el.get_text(strip=True) if salary_el else "",
                                "requirements": [],
                                "headcount": 1,
                                "posted_date": "",
                                "url": title_el.get("href", ""),
                                "skills": [],
                            }
                            jobs.append(self._normalize_job(job, "domestic", keyword))
                    except Exception:
                        continue
        except Exception as e:
            self.logger.error(f"[智联] 采集异常: {e}")

        return jobs[:100]
