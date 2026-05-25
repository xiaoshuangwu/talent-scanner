"""数据处理与聚合模块"""

import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta


class DataAggregator:
    """数据聚合器：对采集到的原始岗位数据进行统计分析"""

    def __init__(self, config):
        self.config = config
        self.categories = config.get("categories", {})

    def aggregate(self, jobs: list, report_date: str) -> dict:
        """
        聚合分析岗位数据

        Returns:
            dict: 包含以下分析维度:
                - summary: 总体概览
                - by_region: 按区域（国内/国际）
                - by_platform: 按平台
                - by_category: 按职位类别
                - by_location: 按城市/地区
                - top_companies: 招聘最多的公司
                - top_skills: 最热门技能
                - top_keywords: 需求最高的职位关键词
                - salary_analysis: 薪资分析
                - trends: 趋势数据（如有历史数据）
        """
        if not jobs:
            return self._empty_report(report_date)

        # 基本统计
        total_jobs = len(jobs)
        total_headcount = sum(j.get("headcount", 1) for j in jobs)
        unique_companies = len(set(j.get("company", "") for j in jobs if j.get("company")))

        # 按区域统计
        domestic = [j for j in jobs if j.get("region") == "domestic"]
        international = [j for j in jobs if j.get("region") == "international"]

        # 按平台统计
        by_platform = self._count_by(jobs, "platform")

        # 按类别统计
        category_counts = self._count_by(jobs, "category")

        # 按城市统计
        location_counts = self._count_by(jobs, "location")

        # Top公司
        company_counts = Counter(j.get("company", "") for j in jobs if j.get("company"))
        top_companies = [
            {"name": name, "jobs": count, "estimated_headcount": self._company_headcount(name, jobs)}
            for name, count in company_counts.most_common(20)
        ]

        # Top技能
        all_skills = []
        for j in jobs:
            skills = j.get("skills", [])
            if isinstance(skills, list):
                all_skills.extend(skills)
        skill_counts = Counter(all_skills)
        top_skills_n = self.config.get("report.top_skills_n", 20)
        top_skills = [{"name": name, "count": count} for name, count in skill_counts.most_common(top_skills_n)]

        # Top关键词（职位标题高频词）
        title_words = self._extract_title_keywords(jobs)
        top_keywords = [{"word": w, "count": c} for w, c in title_words.most_common(30)]

        # 薪资分析
        salary_analysis = self._analyze_salary(jobs)

        # 类别详细统计
        category_detail = {}
        for cat, cat_jobs in self._group_by_category(jobs).items():
            cat_companies = len(set(j.get("company", "") for j in cat_jobs if j.get("company")))
            cat_headcount = sum(j.get("headcount", 1) for j in cat_jobs)
            category_detail[cat] = {
                "jobs": len(cat_jobs),
                "companies": cat_companies,
                "estimated_headcount": cat_headcount,
                "percentage": round(len(cat_jobs) / total_jobs * 100, 1) if total_jobs else 0,
            }

        return {
            "report_date": report_date,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data_source_count": len(set(j.get("platform", "") for j in jobs)),
            "summary": {
                "total_jobs": total_jobs,
                "total_estimated_headcount": total_headcount,
                "unique_companies": unique_companies,
            },
            "by_region": {
                "domestic": {
                    "jobs": len(domestic),
                    "headcount": sum(j.get("headcount", 1) for j in domestic),
                    "platforms": len(set(j.get("platform", "") for j in domestic)),
                },
                "international": {
                    "jobs": len(international),
                    "headcount": sum(j.get("headcount", 1) for j in international),
                    "platforms": len(set(j.get("platform", "") for j in international)),
                },
            },
            "by_platform": {k: v for k, v in sorted(by_platform.items(), key=lambda x: x[1], reverse=True)},
            "by_category": {k: v for k, v in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)},
            "by_location": {k: v for k, v in sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:20]},
            "top_companies": top_companies,
            "top_skills": top_skills,
            "top_keywords": top_keywords,
            "salary_analysis": salary_analysis,
            "category_detail": category_detail,
            "raw_count": total_jobs,
        }

    def _count_by(self, jobs: list, key: str) -> dict:
        """按指定字段计数"""
        counter = Counter()
        for j in jobs:
            val = j.get(key, "")
            if val:
                counter[val] += 1
        return dict(counter)

    def _company_headcount(self, company_name: str, jobs: list) -> int:
        """估算某公司的招聘总人数"""
        return sum(j.get("headcount", 1) for j in jobs if j.get("company") == company_name)

    def _group_by_category(self, jobs: list) -> dict:
        """按类别分组"""
        groups = defaultdict(list)
        for j in jobs:
            cat = j.get("category", "其他")
            groups[cat].append(j)
        return dict(groups)

    def _extract_title_keywords(self, jobs: list) -> Counter:
        """从职位标题提取高频关键词"""
        stopwords = {"the", "a", "an", "in", "of", "and", "or", "for", "to", "is", "at",
                     "工程师", "开发", "经理", "高级", "资深", "senior", "engineer", "developer"}
        word_counter = Counter()
        for j in jobs:
            title = j.get("title", "")
            # 中英文分词（简单方式）
            words = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{2,}', title)
            for w in words:
                if w.lower() not in stopwords and len(w) > 1:
                    word_counter[w] += 1
        return word_counter

    def _analyze_salary(self, jobs: list) -> dict:
        """薪资分析"""
        salaries = []
        for j in jobs:
            salary = j.get("salary", "")
            if salary:
                monthly = self._parse_salary(salary)
                if monthly:
                    salaries.append(monthly)

        if not salaries:
            return {"has_data": False, "count": 0, "note": "薪资数据不足"}

        salaries.sort()
        return {
            "has_data": True,
            "count": len(salaries),
            "min": salaries[0],
            "max": salaries[-1],
            "median": salaries[len(salaries) // 2],
            "avg": round(sum(salaries) / len(salaries), 0),
        }

    def _parse_salary(self, salary_str: str) -> float:
        """解析薪资字符串为月薪（K）"""
        # 匹配 "15K-25K" 或 "15000-25000" 或 "$80K-$120K"
        salary_str = str(salary_str).replace(",", "")

        # 美元年薪转为月薪K
        if "$" in salary_str:
            match = re.search(r'\$(\d+)K?\s*-\s*\$?(\d+)K?', salary_str, re.IGNORECASE)
            if match:
                low, high = float(match.group(1)), float(match.group(2))
                # 年薪转月薪并转K
                return (low + high) / 2 / 12

        # 人民币月薪K
        match = re.search(r'(\d+)\s*[Kk]\s*-\s*(\d+)\s*[Kk]', salary_str)
        if match:
            low, high = float(match.group(1)), float(match.group(2))
            return (low + high) / 2

        # 数字范围（可能是元）
        match = re.search(r'(\d+)\s*-\s*(\d+)', salary_str)
        if match:
            low, high = float(match.group(1)), float(match.group(2))
            if low > 100:  # 可能是元
                return (low + high) / 2 / 1000
            return (low + high) / 2

        # 单个数字
        match = re.search(r'(\d+)', salary_str)
        if match:
            val = float(match.group(1))
            return val / 1000 if val > 100 else val

        return 0

    def _empty_report(self, date: str) -> dict:
        """空报告"""
        return {
            "report_date": date,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data_source_count": 0,
            "summary": {"total_jobs": 0, "total_estimated_headcount": 0, "unique_companies": 0},
            "by_region": {},
            "by_platform": {},
            "by_category": {},
            "by_location": {},
            "top_companies": [],
            "top_skills": [],
            "top_keywords": [],
            "salary_analysis": {"has_data": False},
            "category_detail": {},
            "raw_count": 0,
        }
