"""演示数据生成器 - 当实际爬虫无法工作时生成模拟数据用于报告展示"""

import random
from datetime import datetime, timedelta


class DemoDataGenerator:
    """生成演示数据，方便快速查看报告效果"""

    COMPANIES_CN = [
        "字节跳动", "腾讯", "阿里巴巴", "百度", "美团", "京东", "网易", "小米", "拼多多", "滴滴",
        "华为", "商汤科技", "科大讯飞", "海康威视", "大疆", "蚂蚁集团", "快手", "小红书", "哔哩哔哩", "知乎",
    ]
    COMPANIES_GLOBAL = [
        "Google", "Microsoft", "Amazon", "Apple", "Meta", "Netflix", "Tesla", "OpenAI",
        "Anthropic", "Stripe", "Uber", "Airbnb", "Spotify", "Snowflake", "Databricks",
        "ByteDance", "TikTok", "NVIDIA", "AMD", "Intel",
    ]

    JOB_TITLES_CN = [
        ("AI算法工程师", "AI与数据", ["Python", "PyTorch", "TensorFlow", "深度学习", "NLP"]),
        ("Java后端开发工程师", "Web与移动", ["Java", "Spring Boot", "微服务", "MySQL", "Redis"]),
        ("Python开发工程师", "AI与数据", ["Python", "Django", "Flask", "PostgreSQL", "Docker"]),
        ("前端开发工程师", "Web与移动", ["React", "Vue", "TypeScript", "CSS", "Webpack"]),
        ("数据科学家", "AI与数据", ["Python", "SQL", "Spark", "机器学习", "统计学"]),
        ("DevOps工程师", "云计算与DevOps", ["Kubernetes", "Docker", "CI/CD", "Jenkins", "Terraform"]),
        ("产品经理", "产品与管理", ["需求分析", "PRD", "数据分析", "用户研究", "敏捷"]),
        ("测试开发工程师", "测试与质量", ["Python", "Selenium", "自动化测试", "性能测试"]),
        ("大数据开发工程师", "AI与数据", ["Hadoop", "Spark", "Flink", "Hive", "Kafka"]),
        ("安全工程师", "安全", ["渗透测试", "安全审计", "WAF", "SOC", "漏洞挖掘"]),
        ("移动端开发工程师", "Web与移动", ["Flutter", "React Native", "iOS", "Android", "Swift"]),
        ("云原生架构师", "云计算与DevOps", ["Kubernetes", "Service Mesh", "Go", "Istio", "Helm"]),
        ("NLP算法工程师", "AI与数据", ["NLP", "Transformer", "BERT", "GPT", "大模型"]),
        ("计算机视觉工程师", "AI与数据", ["OpenCV", "PyTorch", "CNN", "目标检测", "图像分割"]),
        ("全栈开发工程师", "Web与移动", ["React", "Node.js", "TypeScript", "MongoDB", "Docker"]),
    ]
    JOB_TITLES_GLOBAL = [
        ("Senior Software Engineer", "Web与移动", ["Java", "Go", "AWS", "Distributed Systems"]),
        ("Machine Learning Engineer", "AI与数据", ["Python", "PyTorch", "MLOps", "GPU"]),
        ("Full Stack Developer", "Web与移动", ["React", "Node.js", "TypeScript", "GraphQL"]),
        ("Data Scientist", "AI与数据", ["Python", "SQL", "A/B Testing", "Statistics"]),
        ("DevOps Engineer", "云计算与DevOps", ["Kubernetes", "Terraform", "CI/CD", "Monitoring"]),
        ("Product Manager", "产品与管理", ["Roadmap", "Analytics", "User Research", "OKR"]),
        ("AI Research Scientist", "AI与数据", ["PyTorch", "Transformers", "RLHF", "Research"]),
        ("Cloud Architect", "云计算与DevOps", ["AWS", "Azure", "GCP", "Microservices"]),
        ("Security Engineer", "安全", ["Penetration Testing", "Threat Modeling", "SIEM"]),
        ("Platform Engineer", "云计算与DevOps", ["Kubernetes", "Go", "Internal Tools", "API Design"]),
        ("iOS Developer", "Web与移动", ["Swift", "SwiftUI", "UIKit", "Combine"]),
        ("Data Engineer", "AI与数据", ["Spark", "Kafka", "Airflow", "Data Lake", "SQL"]),
    ]

    CITIES_CN = ["北京", "上海", "深圳", "杭州", "广州", "成都", "南京", "武汉"]
    CITIES_GLOBAL = ["San Francisco, CA", "New York, NY", "London, UK", "Berlin, DE",
                     "Singapore", "Tokyo, JP", "Toronto, CA", "Seattle, WA"]

    SALARY_RANGES_CN = [
        "15K-25K", "20K-35K", "25K-40K", "30K-50K", "35K-55K",
        "40K-60K", "50K-80K", "15K-20K", "12K-18K", "18K-30K",
    ]
    SALARY_RANGES_GLOBAL = [
        "$120K-$180K", "$150K-$220K", "$100K-$150K", "$180K-$280K",
        "$90K-$130K", "$140K-$200K", "$200K-$300K", "$130K-$190K",
    ]

    def __init__(self, logger):
        self.logger = logger

    def generate(self, count: int = 300) -> list:
        """生成指定数量的模拟岗位数据"""
        self.logger.info(f"🎲 生成 {count} 条模拟数据...")

        jobs = []
        today = datetime.now()

        for i in range(count):
            # 60%国内 40%国际
            is_domestic = random.random() < 0.6

            if is_domestic:
                title_info = random.choice(self.JOB_TITLES_CN)
                company = random.choice(self.COMPANIES_CN)
                city = random.choice(self.CITIES_CN)
                salary = random.choice(self.SALARY_RANGES_CN)
                region = "domestic"
                platform = random.choice(["boss_zhipin", "liepin", "zhilian", "lagou"])
            else:
                title_info = random.choice(self.JOB_TITLES_GLOBAL)
                company = random.choice(self.COMPANIES_GLOBAL)
                city = random.choice(self.CITIES_GLOBAL)
                salary = random.choice(self.SALARY_RANGES_GLOBAL)
                region = "international"
                platform = random.choice(["linkedin", "indeed", "glassdoor"])

            title, category, skills = title_info

            # 发布日期随机取最近7天
            days_ago = random.randint(0, 7)
            posted = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")

            # 招聘人数估计（热招职位的招聘人数更多）
            headcount = random.choices([1, 2, 3, 5, 10], weights=[40, 30, 15, 10, 5])[0]

            job = {
                "title": title,
                "company": company,
                "location": city,
                "salary": salary,
                "requirements": skills[:3],
                "headcount": headcount,
                "posted_date": posted,
                "platform": platform,
                "region": region,
                "url": "",
                "category": category,
                "skills": skills,
                "search_keyword": title.split()[0],
            }
            jobs.append(job)

        # 按公司名称排序，让数据看起来更真实（大公司岗位多）
        jobs.sort(key=lambda x: (x["company"], x["title"]))

        self.logger.info(f"✅ 模拟数据生成完成: {len(jobs)} 条")
        return jobs
