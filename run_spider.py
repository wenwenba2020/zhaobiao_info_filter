#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
招标信息采集爬虫主程序
"""

import os
import sys
from datetime import datetime
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def setup_logger():
    """配置日志记录器"""
    log_path = os.path.join("logs", f"spider_{datetime.now().strftime('%Y%m%d')}.log")
    os.makedirs("logs", exist_ok=True)
    
    logger.add(
        log_path,
        rotation="500 MB",
        encoding="utf-8",
        enqueue=True,
        compression="zip",
        retention="10 days"
    )

def setup_chrome_driver():
    """配置Chrome浏览器驱动"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def main():
    """主程序入口"""
    try:
        # 配置日志
        setup_logger()
        logger.info("启动招标信息采集爬虫...")
        
        # 配置浏览器
        driver = setup_chrome_driver()
        logger.info("Chrome浏览器驱动初始化成功")
        
        # TODO: 实现爬虫主要逻辑
        
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        sys.exit(1)
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    main()