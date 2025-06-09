#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Chrome驱动修复工具
用于下载和配置与当前Chrome浏览器版本匹配的WebDriver
"""

import os
import sys
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def setup_logger():
    """配置日志记录器"""
    os.makedirs("logs", exist_ok=True)
    logger.add(
        os.path.join("logs", "chrome_driver_fix.log"),
        rotation="100 MB",
        encoding="utf-8",
        enqueue=True,
        compression="zip",
        retention="10 days"
    )

def main():
    """主程序入口"""
    try:
        # 配置日志
        setup_logger()
        logger.info("开始修复Chrome驱动...")
        
        # 下载并安装最新的ChromeDriver
        driver_path = ChromeDriverManager().install()
        logger.info(f"ChromeDriver已安装到: {driver_path}")
        
        # 测试驱动是否正常工作
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service)
        driver.quit()
        
        logger.info("Chrome驱动修复成功！")
        print("Chrome驱动修复成功！")
        return 0
        
    except Exception as e:
        logger.error(f"Chrome驱动修复失败: {str(e)}")
        print(f"错误: Chrome驱动修复失败 - {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())