"""拉勾爬虫"""

from scraper.base import BaseScraper


class LagouScraper(BaseScraper):
    """拉勾 - 页面解析采集"""

    def __init__(self, config, global_cfg, logger):
        super().__init__("lagou", config, global_cfg, logger)
        self.base_url = config.get("base_url", "https://www.lagou.com")

    def search_jobs(self, keyword: str, location: str = None) -> list:
        jobs = []
        try:
            url = f"{self.base_url}/jobs/list_{keyword}"
            headers = {"Referer": "https://www.lagou.com/"}
            resp = self._safe_request(url, headers=headers)
            if resp:
                soup = self._parse_html(resp.text)
                cards = soup.select(".item-con-list, .con_list_item, .position-item")

                for card in cards:
                    title_el = card.select_one("h3, .position-name, .p_top a")
                    company_el = card.select_one(".company-name, .company_name")
                    salary_el = card.select_one(".money, .salary")

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

        except Exception as e:
            self.logger.error(f"[拉勾] 采集异常: {e}")

        return jobs[:100]
