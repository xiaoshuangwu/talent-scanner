"""配置管理模块"""

import os
import yaml


class Config:
    """配置文件加载与访问"""

    def __init__(self, config_path: str):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        with open(config_path, "r", encoding="utf-8") as f:
            self._data = yaml.safe_load(f)

    def get(self, key: str, default=None):
        """通过点分隔路径获取配置值，如 'global.output_dir'"""
        keys = key.split(".")
        value = self._data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value):
        """设置配置值"""
        keys = key.split(".")
        target = self._data
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value

    @property
    def domestic_platforms(self):
        return self._data.get("domestic", {})

    @property
    def international_platforms(self):
        return self._data.get("international", {})

    @property
    def all_platforms(self):
        """返回所有启用的平台配置列表"""
        platforms = []
        for region in ["domestic", "international"]:
            for name, cfg in self._data.get(region, {}).items():
                if cfg.get("enabled", False):
                    platforms.append({
                        "name": name,
                        "region": region,
                        "config": cfg
                    })
        return platforms
