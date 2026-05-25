"""Glassdoor爬虫"""

from scraper.base import BaseScraper


class GlassdoorScraper(BaseScraper):
    """Glassdoor"""

    def __init__(self, config, global_cfg, logger):
        super().__init__("glassdoor", config, global_cfg, logger)
        self.base_url = config.get("base_url", "https://www.glassdoor.com")

    def search_jobs(self, keyword: str, location: str = None) -> list:
        jobs = []
        try:
            url = f"{self.base_url}/Job/jobs.htm"
            params = {"sc.keyword": keyword}
            if location:
                params["locT"] = "N"
                params["locId"] = location

            resp = self._safe_request(url, params=params)
            if resp:
                soup = self._parse_html(resp.text)
                cards = soup.select(".jobListing, .react-job-listing, [data-test='jobListing']")

                for card in cards:
                    title_el = card.select_one(".job-title, a.jobLink, [data-test='job-link']")
                    company_el = card.select_one(".employer-name, [data-test='employer-name']")
                    location_el = card.select_one(".location, [data-test='location']")

                    if title_el:
                        job = {
                            "title": title_el.get_text(strip=True),
                            "company": company_el.get_text(strip=True) if company_el else "",
                            "location": location_el.get_text(strip=True) if location_el else (location or ""),
                            "salary": "",
                            "requirements": [],
                            "headcount": 1,
                            "posted_date": "",
                            "url": title_el.get("href", ""),
                            "skills": [],
                        }
                        jobs.append(self._normalize_job(job, "international", keyword))

        except Exception as e:
            self.logger.error(f"[Glassdoor] 采集异常: {e}")

        return jobs[:100]
