#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
招标信息采集系统测试脚本
"""

import os
import sys
import unittest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from loguru import logger

class TestSpider(unittest.TestCase):
    """爬虫功能测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        # 配置日志
        os.makedirs("logs", exist_ok=True)
        logger.add(
            os.path.join("logs", "test.log"),
            rotation="100 MB",
            encoding="utf-8",
            enqueue=True,
            compression="zip",
            retention="10 days"
        )
        
        # 配置浏览器
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--headless")  # 无头模式
        
        service = Service(ChromeDriverManager().install())
        cls.driver = webdriver.Chrome(service=service, options=chrome_options)
    
    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        cls.driver.quit()
    
    def test_chrome_driver(self):
        """测试Chrome驱动是否正常工作"""
        try:
            self.driver.get("https://www.baidu.com")
            self.assertIn("百度", self.driver.title)
            logger.info("Chrome驱动测试通过")
        except Exception as e:
            logger.error(f"Chrome驱动测试失败: {str(e)}")
            raise
    
    def test_project_structure(self):
        """测试项目结构是否完整"""
        required_dirs = [
            "config",
            "data",
            "data/attachments",
            "data/processed",
            "data/raw",
            "data/saved_pages",
            "data/scraped_pages",
            "drivers",
            "logs",
            "src",
            "src/utils"
        ]
        
        for dir_path in required_dirs:
            self.assertTrue(
                os.path.exists(dir_path),
                f"目录不存在: {dir_path}"
            )
            logger.info(f"目录检查通过: {dir_path}")

def main():
    """测试入口"""
    try:
        unittest.main()
    except Exception as e:
        logger.error(f"测试运行失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()