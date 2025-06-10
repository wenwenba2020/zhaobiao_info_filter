#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
招标信息自动抓取脚本
基于个性化项目定制功能的完整爬虫实现

Author: Assistant
Date: 2025-06-09
"""

import json
import time
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
import shutil
import ftplib
import logging

# 第三方库导入
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException
)
from bs4 import BeautifulSoup
import requests


class ZhaobiaoSpider:
    """招标信息爬虫主类"""
    
    def __init__(self):
        """初始化爬虫"""
        self.config = self.load_config()
        self.driver = None
        self.wait_time = self.config['basic_config']['wait_time']
        self.logger = self.setup_logger()
        
        # 确保必要的目录存在
        self.ensure_directories()
    
    def load_config(self):
        """加载配置文件"""
        try:
            config_path = Path("config/settings.json")
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 配置文件加载失败: {e}")
            sys.exit(1)
    
    def setup_logger(self):
        """设置日志记录"""
        logger = logging.getLogger('zhaobiao_spider')
        logger.setLevel(getattr(logging, self.config['basic_config']['log_level']))
        
        # 创建日志处理器
        log_file = Path("logs") / f"spider_{datetime.now().strftime('%Y%m%d')}.log"
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setLevel(logging.INFO)
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            "logs",
            "data/scraped_pages",
            "data/processed",
            "data/attachments"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def system_check(self):
        """系统自检"""
        print("\n" + "="*80)
        print("🔧 系统自检开始")
        print("="*80)
        
        checks = []
        
        # 1. 检查Python版本
        try:
            python_version = sys.version.split()[0]
            print(f"✅ Python版本: {python_version}")
            checks.append(True)
        except Exception as e:
            print(f"❌ Python版本检查失败: {e}")
            checks.append(False)
        
        # 2. 检查必要目录
        try:
            for directory in ["config", "data", "logs"]:
                if Path(directory).exists():
                    print(f"✅ 目录存在: {directory}")
                else:
                    print(f"❌ 目录缺失: {directory}")
                    checks.append(False)
            if all(Path(d).exists() for d in ["config", "data", "logs"]):
                checks.append(True)
        except Exception as e:
            print(f"❌ 目录检查失败: {e}")
            checks.append(False)
        
        # 3. 检查配置文件
        try:
            config_files = ["config/settings.json"]
            for config_file in config_files:
                if Path(config_file).exists():
                    print(f"✅ 配置文件存在: {config_file}")
                else:
                    print(f"❌ 配置文件缺失: {config_file}")
                    checks.append(False)
            if all(Path(f).exists() for f in config_files):
                checks.append(True)
        except Exception as e:
            print(f"❌ 配置文件检查失败: {e}")
            checks.append(False)
        
        # 4. 检查ChromeDriver
        try:
            driver_path = Path("drivers") / "chromedriver.exe"
            if driver_path.exists():
                print(f"✅ ChromeDriver存在: {driver_path}")
                checks.append(True)
            else:
                print(f"⚠️  ChromeDriver未找到，将尝试自动下载")
                checks.append(True)  # 允许自动下载
        except Exception as e:
            print(f"❌ ChromeDriver检查失败: {e}")
            checks.append(False)
        
        # 5. 检查FTP连接
        try:
            ftp_config = self.config['ftp_config']
            with ftplib.FTP() as ftp:
                ftp.connect(ftp_config['host'], ftp_config['port'], timeout=10)
                ftp.login(ftp_config['username'], ftp_config['password'])
                print(f"✅ FTP连接正常: {ftp_config['host']}")
                checks.append(True)
        except Exception as e:
            print(f"❌ FTP连接失败: {e}")
            checks.append(False)
        
        success_rate = sum(checks) / len(checks) * 100
        print(f"\n📊 自检完成，成功率: {success_rate:.1f}% ({sum(checks)}/{len(checks)})")
        
        if success_rate < 80:
            print("❌ 自检失败，请解决上述问题后重试")
            return False
        
        print("✅ 系统自检通过，可以继续执行")
        return True
    
    def setup_driver(self):
        """设置Chrome浏览器驱动"""
        print("\n🔧 正在设置浏览器驱动...")
        
        try:
            # 设置Chrome选项
            chrome_options = Options()
            browser_config = self.config.get('browser_config', {})
            
            if browser_config.get('headless', False):
                chrome_options.add_argument('--headless')
            
            # 添加Chrome选项
            for option in browser_config.get('chrome_options', []):
                chrome_options.add_argument(option)
            
            # 设置窗口大小
            window_size = browser_config.get('window_size', [1920, 1080])
            chrome_options.add_argument(f'--window-size={window_size[0]},{window_size[1]}')
            
            # 优先使用本地ChromeDriver
            local_driver_path = Path("drivers") / "chromedriver.exe"
            if local_driver_path.exists():
                print(f"✅ 使用本地ChromeDriver: {local_driver_path}")
                service = Service(str(local_driver_path))
            else:
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    service = Service(ChromeDriverManager().install())
                    print("✅ 使用自动下载的ChromeDriver")
                except Exception as e:
                    print(f"❌ ChromeDriver设置失败: {e}")
                    return False
            
            # 创建WebDriver实例
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print("✅ 浏览器驱动设置成功")
            return True
            
        except Exception as e:
            print(f"❌ 浏览器驱动设置失败: {e}")
            self.logger.error(f"浏览器驱动设置失败: {e}")
            return False
    
    def prompt_user_login(self):
        """提示用户登录"""
        print("\n" + "="*60)
        print("🔐 用户登录阶段")
        print("="*60)
        print("1. 请在打开的浏览器中登录 zhaobiao.cn")
        print("2. 确保登录成功后能看到用户信息")
        print("3. 登录完成后，回到此窗口确认")
        print("="*60)
        
        try:
            # 打开网站
            target_url = self.config['basic_config']['target_url']
            print(f"🌐 正在打开网站: {target_url}")
            self.driver.get(target_url)
            
            # 等待用户手动登录
            while True:
                user_input = input("\n⏳ 登录完成后输入 'y' 确认，输入 'q' 退出: ").strip().lower()
                
                if user_input == 'q':
                    print("👋 用户选择退出")
                    return False
                elif user_input == 'y':
                    # 检查登录状态
                    if self.check_login_status():
                        print("✅ 登录确认成功")
                        return True
                    else:
                        print("❌ 登录检查失败，请重新登录")
                        continue
                else:
                    print("⚠️  请输入 'y' 确认登录或 'q' 退出")
                    
        except Exception as e:
            print(f"❌ 登录过程失败: {e}")
            self.logger.error(f"登录过程失败: {e}")
            return False
    
    def check_login_status(self):
        """检查登录状态"""
        print("🔍 正在检查登录状态...")
        
        try:
            # 刷新页面获取最新状态
            self.driver.refresh()
            time.sleep(3)
            
            # 检查登录标识
            login_indicators = [
                "会员中心",
                "用户中心", 
                "个人中心",
                "退出登录",
                "登出",
                ".user-info",
                ".user-center",
                ".member-center"
            ]
            
            page_source = self.driver.page_source
            
            for indicator in login_indicators:
                if indicator.startswith('.'):
                    # CSS选择器
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, indicator)
                        if elements and any(elem.is_displayed() for elem in elements):
                            print(f"✅ 发现登录标识: {indicator}")
                            return True
                    except:
                        continue
                else:
                    # 文本检查
                    if indicator in page_source:
                        print(f"✅ 发现会员中心链接，用户已登录")
                        return True
            
            print("❌ 未发现登录标识，请确认已正确登录")
            return False
            
        except Exception as e:
            print(f"❌ 登录状态检查失败: {e}")
            return False
    
    def navigate_to_member_center(self):
        """导航到会员中心"""
        print("\n🏠 正在导航到会员中心...")
        
        try:
            member_center_url = self.config['member_center_config']['member_center_url']
            print(f"🌐 正在访问: {member_center_url}")
            
            self.driver.get(member_center_url)
            time.sleep(3)
            
            # 检查是否成功进入会员中心
            if "会员中心" in self.driver.page_source or "homePageUc" in self.driver.current_url:
                print("✅ 成功进入会员中心")
                return True
            else:
                print("❌ 进入会员中心失败")
                return False
                
        except Exception as e:
            print(f"❌ 导航到会员中心失败: {e}")
            self.logger.error(f"导航到会员中心失败: {e}")
            return False
    
    def navigate_to_customize(self):
        """进入个性化项目定制页面"""
        print("\n🎯 正在进入个性化项目定制...")
        
        try:
            customize_url = self.config['member_center_config']['customize_url']
            print(f"🌐 正在访问: {customize_url}")
            
            self.driver.get(customize_url)
            time.sleep(3)
            
            # 检查是否成功进入定制页面
            if "定制" in self.driver.page_source or "ucFocusCustomize" in self.driver.current_url:
                print("✅ 成功进入个性化项目定制页面")
                return True
            else:
                print("❌ 进入个性化项目定制页面失败")
                return False
                
        except Exception as e:
            print(f"❌ 进入个性化项目定制页面失败: {e}")
            self.logger.error(f"进入个性化项目定制页面失败: {e}")
            return False
    
    def process_condition(self, condition_num):
        """处理指定的定制条件"""
        print(f"\n📋 正在处理定制条件{condition_num:02d}...")
        
        try:
            # 构建条件URL
            condition_url = f"https://center.zhaobiao.cn/www/ucFocusCustomize/listOrder?keyNo={condition_num}"
            print(f"🌐 正在访问: {condition_url}")
            
            self.driver.get(condition_url)
            time.sleep(3)
            
            # 设置时间范围
            if not self.set_time_range():
                print("⚠️  时间范围设置失败，但继续执行")
            
            # 点击搜索按钮
            if not self.click_search_button():
                print("⚠️  搜索按钮点击失败，但继续执行")
            
            # 爬取搜索结果
            return self.scrape_results(condition_num)
            
        except Exception as e:
            print(f"❌ 处理定制条件{condition_num:02d}失败: {e}")
            self.logger.error(f"处理定制条件{condition_num:02d}失败: {e}")
            return False
    
    def set_time_range(self):
        """设置时间范围为最近指定天数"""
        print("📅 正在设置时间范围...")
        
        try:
            # 计算时间范围
            end_date = datetime.now()
            days_range = self.config['search_config']['condition_01']['time_range']
            start_date = end_date - timedelta(days=days_range)
            
            start_time_str = start_date.strftime('%Y-%m-%d')
            end_time_str = end_date.strftime('%Y-%m-%d')
            
            print(f"⏰ 设置时间范围: {start_time_str} 至 {end_time_str}")
            
            # 等待页面加载
            time.sleep(2)

            # 查找时间输入框（使用通用选择器）
            time_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")

            # 寻找自定义时间区域的输入框
            start_input = None
            end_input = None

            # 方法1：通过位置查找
            for i, input_elem in enumerate(time_inputs):
                try:
                    if input_elem.is_displayed():
                        # 检查输入框是否在时间范围区域内
                        parent_text = input_elem.find_element(By.XPATH, "../..").text
                        if "自定义" in parent_text or "时间范围" in parent_text:
                            if start_input is None:
                                start_input = input_elem
                                print(f"✅ 找到开始时间输入框")
                            elif end_input is None:
                                end_input = input_elem
                                print(f"✅ 找到结束时间输入框")
                                break
                except:
                    continue

            # 方法2：如果方法1失败，尝试使用onclick属性查找
            if not start_input or not end_input:
                print("🔄 尝试通过onclick属性查找时间输入框...")
                wdate_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[onclick*='WdatePicker']")
                if len(wdate_inputs) >= 2:
                    start_input = wdate_inputs[0]
                    end_input = wdate_inputs[1]
                    print("✅ 通过onclick属性找到时间输入框")

            # 方法3：如果还是失败，尝试使用CSS类名
            if not start_input or not end_input:
                print("🔄 尝试通过CSS类名查找时间输入框...")
                wdate_inputs = self.driver.find_elements(By.CSS_SELECTOR, ".Wdate")
                if len(wdate_inputs) >= 2:
                    start_input = wdate_inputs[0]
                    end_input = wdate_inputs[1]
                    print("✅ 通过CSS类名找到时间输入框")

            if not start_input or not end_input:
                print("⚠️  未找到时间输入框，跳过时间设置")
                return True  # 不作为致命错误，继续执行

            # 设置开始时间
            self.driver.execute_script("arguments[0].focus();", start_input)
            start_input.clear()
            start_input.send_keys(start_time_str)
            time.sleep(1)

            # 设置结束时间
            self.driver.execute_script("arguments[0].focus();", end_input)
            end_input.clear()
            end_input.send_keys(end_time_str)
            time.sleep(1)

            print("✅ 时间范围设置成功")
            self.logger.info(f"时间范围设置成功: {start_time_str} 至 {end_time_str}")
            return True

        except Exception as e:
            print(f"❌ 时间范围设置失败: {e}")
            self.logger.error(f"时间范围设置失败: {e}")
            print("⚠️  继续执行后续步骤...")
            return True  # 不作为致命错误

    def click_search_button(self):
        """点击搜索按钮"""
        print("🔍 正在点击搜索按钮...")

        try:
            # 等待页面稳定
            time.sleep(2)

            # 方法1：使用JavaScript直接查找搜索按钮
            js_script = """
            // 查找包含"搜索"文本的所有元素
            var elements = document.querySelectorAll('*');
            for (var i = 0; i < elements.length; i++) {
                var elem = elements[i];
                if ((elem.textContent && elem.textContent.trim() === '搜索') || 
                    (elem.value && elem.value.includes('搜索')) ||
                    (elem.innerHTML && elem.innerHTML.includes('搜索'))) {
                    // 检查元素是否可点击
                    if (elem.tagName === 'BUTTON' || elem.tagName === 'INPUT' ||
                        elem.onclick || elem.style.cursor === 'pointer') {
                        elem.click();
                        return true;
                    }
                }
            }
            return false;
            """

            result = self.driver.execute_script(js_script)
            if result:
                print("✅ 通过JavaScript成功点击搜索按钮")
                time.sleep(3)  # 等待搜索结果加载
                return True

            # 方法2：通过CSS选择器查找
            button_selectors = [
                "div:contains('搜索')",
                "span:contains('搜索')",
                "button:contains('搜索')",
                "a:contains('搜索')",
                "*[onclick*='搜索']",
                "*[onclick*='search']",
                "button[type='submit']",
                "input[type='submit']",
                ".search-btn",
                ".btn-search"
            ]

            for selector in button_selectors:
                try:
                    if ":contains" in selector:
                        # 使用XPath查找包含文本的元素
                        xpath = f"//*[contains(text(), '搜索')]"
                        buttons = self.driver.find_elements(By.XPATH, xpath)
                        
                        for button in buttons:
                            if button.is_displayed() and button.is_enabled():
                                try:
                                    self.driver.execute_script("arguments[0].click();", button)
                                    print("✅ 通过XPath成功点击搜索按钮")
                                    time.sleep(3)
                                    return True
                                except:
                                    continue
                    else:
                        button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if button.is_displayed() and button.is_enabled():
                            self.driver.execute_script("arguments[0].click();", button)
                            print(f"✅ 通过选择器 {selector} 成功点击搜索按钮")
                            time.sleep(3)
                            return True
                except:
                    continue

            # 方法3：查找所有可点击元素并检查文本
            print("🔄 尝试查找所有可点击元素...")
            clickable_elements = self.driver.find_elements(By.CSS_SELECTOR,
                "button, input[type='submit'], input[type='button'], a, div[onclick], span[onclick]")

            for element in clickable_elements:
                try:
                    if element.is_displayed():
                        text = element.text.strip()
                        if text == "搜索" or "搜索" in text:
                            self.driver.execute_script("arguments[0].click();", element)
                            print(f"✅ 找到并点击搜索按钮: {text}")
                            time.sleep(3)
                            return True
                except:
                    continue

            print("⚠️  未找到搜索按钮，但页面可能已经显示结果")
            # 检查是否已经有搜索结果
            try:
                results_table = self.driver.find_element(By.CSS_SELECTOR, "table")
                if results_table.is_displayed():
                    print("✅ 检测到结果表格，认为搜索已执行")
                    return True
            except:
                pass

            print("⚠️  继续执行后续步骤...")
            return True  # 不作为致命错误

        except Exception as e:
            print(f"❌ 搜索按钮点击失败: {e}")
            self.logger.error(f"搜索按钮点击失败: {e}")
            print("⚠️  继续执行后续步骤...")
            return True  # 不作为致命错误

    def scrape_results(self, condition_num):
        """爬取搜索结果 - 逐个保存每个项目的详情页"""
        print(f"📊 正在爬取定制条件{condition_num:02d}的搜索结果...")

        try:
            # 等待结果加载
            time.sleep(5)

            # 提取搜索结果数据
            results_data = self.extract_search_results()

            if not results_data:
                print("⚠️  未找到搜索结果数据")
                return False

            print(f"✅ 成功提取 {len(results_data)} 条招标信息")

            # 生成时间戳
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # 逐个保存每个项目的详情页面
            success_count = 0
            failed_count = 0

            for i, item in enumerate(results_data, 1):
                print(f"\n📄 正在处理第 {i}/{len(results_data)} 个项目...")
                print(f"📝 项目标题: {item['title'][:50]}...")
                print(f"📋 信息类型: {item['info_type']}")
                print(f"📍 地区: {item['area']}")
                print(f"📅 发布时间: {item['pub_date']}")

                # 保存项目详情页面
                if self.save_individual_project(item, condition_num, timestamp):
                    success_count += 1
                    print(f"✅ 项目 {i} 保存成功")
                else:
                    failed_count += 1
                    print(f"❌ 项目 {i} 保存失败")

                # 添加请求间隔，避免请求过于频繁
                time.sleep(self.config['basic_config']['request_delay'])

            # 总结结果
            print(f"\n📊 定制条件{condition_num:02d}处理完成:")
            print(f"✅ 成功: {success_count} 个项目")
            print(f"❌ 失败: {failed_count} 个项目")
            if success_count + failed_count > 0:
                print(f"📈 成功率: {success_count/(success_count+failed_count)*100:.1f}%")

            self.logger.info(f"定制条件{condition_num:02d}处理完成: 成功{success_count}个，失败{failed_count}个")
                           
            return success_count > 0

        except Exception as e:
            print(f"❌ 爬取结果失败: {e}")
            self.logger.error(f"爬取结果失败: {e}")
            return False

    def extract_search_results(self):
        """提取搜索结果数据"""
        try:
            results = []

            # 查找搜索结果表格
            table_selectors = [
                ".custom_table table",
                "table.yhzxtab",
                "#result",
                "tbody#result",
                ".custom_table tbody"
            ]

            table_found = False
            for selector in table_selectors:
                try:
                    if "tbody" in selector or "#result" in selector:
                        # 直接查找tbody
                        rows = self.driver.find_elements(By.CSS_SELECTOR, f"{selector} tr")
                    else:
                        # 查找表格中的数据行
                        rows = self.driver.find_elements(By.CSS_SELECTOR, f"{selector} tbody tr")

                    if rows:
                        print(f"✅ 找到搜索结果表格: {selector} (共{len(rows)}行)")
                        table_found = True
                        break
                except:
                    continue

            if not table_found:
                print("⚠️  未找到搜索结果表格，尝试通用方法...")
                # 尝试查找所有表格行
                rows = self.driver.find_elements(By.CSS_SELECTOR, "table tr")
                if len(rows) > 1:  # 至少有表头和一行数据
                    rows = rows[1:]  # 跳过表头
                    print(f"✅ 使用通用方法找到 {len(rows)} 行数据")
                else:
                    return []

            # 提取每行的数据
            for i, row in enumerate(rows):
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 4:  # 确保有足够的列
                        # 提取项目标题和链接
                        title_cell = cells[0]
                        title_link = title_cell.find_element(By.TAG_NAME, "a")

                        title = title_link.text.strip()
                        link = title_link.get_attribute("href")

                        # 提取其他信息
                        info_type = cells[1].text.strip()
                        area = cells[2].text.strip()
                        pub_date = cells[3].text.strip()

                        result_item = {
                            'index': i + 1,
                            'title': title,
                            'link': link,
                            'info_type': info_type,
                            'area': area,
                            'pub_date': pub_date,
                            'extracted_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }

                        results.append(result_item)

                        if i < 3:  # 显示前3条
                            print(f"📝 项目{i+1}: {title[:50]}...")

                except Exception as e:
                    print(f"⚠️  第{i+1}行数据提取失败: {e}")
                    continue

            return results

        except Exception as e:
            print(f"❌ 搜索结果数据提取失败: {e}")
            return []

    def save_page_locally(self, page_source, filename, current_url):
        """保存页面到本地"""
        try:
            # 创建本地保存目录
            save_dir = Path(self.config['save_config']['local_save_dir'])
            save_dir.mkdir(parents=True, exist_ok=True)

            # 处理HTML内容
            soup = BeautifulSoup(page_source, 'html.parser')

            # 确保页面包含完整的HTML结构
            if not soup.html:
                # 如果没有html标签，添加基本结构
                html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>招标信息搜索结果</title>
    <style>
        body {{ font-family: "Microsoft YaHei", Arial, sans-serif; }}
        .header {{ background: #f5f5f5; padding: 10px; margin-bottom: 20px; }}
        .content {{ padding: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>招标信息搜索结果</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>源链接: <a href="{current_url}">{current_url}</a></p>
    </div>
    <div class="content">
        {page_source}
    </div>
</body>
</html>"""
            else:
                # 添加元信息
                if soup.head:
                    meta_info = soup.new_tag("meta", attrs={"name": "generator", "content": "ZhaobiaoSpider"})
                    soup.head.append(meta_info)

                    meta_time = soup.new_tag("meta", attrs={"name": "generated-time", "content": datetime.now().isoformat()})
                    soup.head.append(meta_time)

                html_content = str(soup)

            # 保存文件
            file_path = save_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"✅ 页面已保存到本地: {file_path}")
            return file_path

        except Exception as e:
            print(f"❌ 本地保存失败: {e}")
            self.logger.error(f"本地保存失败: {e}")
            return None

    def upload_to_ftp(self, local_path, filename):
        """上传文件到FTP服务器"""
        try:
            ftp_config = self.config['ftp_config']
            print(f"📤 正在上传到FTP: {ftp_config['host']}")

            with ftplib.FTP() as ftp:
                # 连接FTP
                ftp.connect(ftp_config['host'], ftp_config['port'])
                ftp.login(ftp_config['username'], ftp_config['password'])

                # 切换到目标目录
                try:
                    ftp.cwd(ftp_config['remote_path'])
                except:
                    # 如果目录不存在，尝试创建
                    try:
                        ftp.mkd(ftp_config['remote_path'])
                        ftp.cwd(ftp_config['remote_path'])
                    except:
                        print(f"⚠️  无法创建目录: {ftp_config['remote_path']}")

                # 上传文件
                with open(local_path, 'rb') as f:
                    ftp.storbinary(f'STOR {filename}', f)

                # 生成访问URL
                remote_url = ftp_config['web_base_url'] + filename

                print(f"✅ 文件上传成功: {filename}")
                return remote_url

        except Exception as e:
            print(f"❌ FTP上传失败: {e}")
            self.logger.error(f"FTP上传失败: {e}")
            return None

    def run(self):
        """运行完整的爬虫流程"""
        print("\n" + "="*80)
        print("🚀 招标信息自动抓取脚本启动")
        print("="*80)

        try:
            # 1. 系统自检
            if not self.system_check():
                return False

            # 2. 设置浏览器驱动
            if not self.setup_driver():
                return False

            # 3. 用户登录
            if not self.prompt_user_login():
                return False

            # 4. 导航到会员中心
            if not self.navigate_to_member_center():
                return False

            # 5. 进入个性化项目定制
            if not self.navigate_to_customize():
                return False

            # 6. 处理定制条件
            success_count = 0
            conditions = [1, 2]  # 定制条件01和02

            for condition_num in conditions:
                if self.process_condition(condition_num):
                    success_count += 1
                    print(f"✅ 定制条件{condition_num:02d}处理成功")
                else:
                    print(f"❌ 定制条件{condition_num:02d}处理失败")

                # 等待间隔
                time.sleep(2)

            # 7. 结果总结
            print("\n" + "="*80)
            print("📋 执行结果总结")
            print("="*80)
            print(f"✅ 成功处理: {success_count}/{len(conditions)} 个定制条件")
            print(f"📊 成功率: {success_count/len(conditions)*100:.1f}%")

            if success_count > 0:
                print("🎉 爬虫执行完成，部分或全部任务成功！")
                return True
            else:
                print("❌ 所有任务失败，请检查配置和网络连接")
                return False

        except Exception as e:
            print(f"❌ 爬虫执行失败: {e}")
            self.logger.error(f"爬虫执行失败: {e}")
            return False

        finally:
            self.cleanup()

    def cleanup(self):
        """清理资源"""
        print("\n🧹 正在清理资源...")

        if self.driver:
            try:
                self.driver.quit()
                print("✅ 浏览器已关闭")
            except:
                pass

        print("✅ 资源清理完成")

    def save_individual_project(self, item, condition_num, timestamp):
        """访问并保存单个项目的详情页面"""
        try:
            # 访问项目详情页
            print(f"🌐 正在访问: {item['link']}")
            self.driver.get(item['link'])

            # 等待页面加载
            time.sleep(3)

            # 获取页面内容
            page_source = self.driver.page_source

            # 生成安全的文件名（包含信息类型和发布时间）
            safe_title = self.sanitize_filename(item['title'][:30])
            safe_info_type = self.sanitize_filename(item['info_type'])
            safe_date = self.sanitize_filename(item['pub_date'])

            # 格式: 信息类型_发布时间_项目标题_项目序号.html
            filename = f"{safe_info_type}_{safe_date}_{safe_title}_{item['index']:03d}.html"

            # 保存项目详情页面到本地
            local_path = self.save_project_detail_page(page_source, filename, item)

            if local_path:
                # 上传到FTP
                remote_url = self.upload_to_ftp(local_path, filename)

                if remote_url:
                    print(f"🌐 上传完成: {remote_url}")
                    return True

            return False

        except Exception as e:
            print(f"❌ 保存个人项目失败: {e}")
            self.logger.error(f"保存个人项目失败: {e}")
            return False

    def sanitize_filename(self, filename):
        """清理文件名，移除非法字符"""
        import re
        # 移除HTML标签
        filename = re.sub(r'<[^>]+>', '', filename)
        # 移除非法字符
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # 替换空格和特殊字符
        filename = re.sub(r'[\s\u3000]+', '_', filename)
        # 移除连续的下划线
        filename = re.sub(r'_+', '_', filename)
        # 移除开头和结尾的下划线
        filename = filename.strip('_')
        # 限制长度
        if len(filename) > 50:
            filename = filename[:50]
        # 确保文件名不为空
        if not filename:
            filename = "untitled"
        return filename

    def save_project_detail_page(self, page_source, filename, item):
        """保存项目详情页面到本地"""
        try:
            save_dir = Path(self.config['save_config']['local_save_dir'])
            save_dir.mkdir(parents=True, exist_ok=True)

            # 处理HTML内容
            soup = BeautifulSoup(page_source, 'html.parser')

            # 添加项目元信息到页面头部
            if soup.head:
                # 添加项目元信息
                meta_tags = [
                    ("project-title", item['title']),
                    ("info-type", item['info_type']),
                    ("area", item['area']),
                    ("publish-date", item['pub_date']),
                    ("source-url", item['link']),
                    ("generated-time", datetime.now().isoformat()),
                    ("generator", "ZhaobiaoSpider"),
                    ("charset", "UTF-8")
                ]

                for name, content in meta_tags:
                    meta_tag = soup.new_tag("meta", attrs={"name": name, "content": str(content)})
                    soup.head.append(meta_tag)

            # 在页面顶部添加美化的项目信息展示区
            if soup.body:
                info_header = soup.new_tag("div", style="""
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    margin: 0 0 20px 0;
                    border-radius: 8px;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                    font-family: 'Microsoft YaHei', Arial, sans-serif;
                """)

                info_content = soup.new_tag("div")
                info_content.append(soup.new_tag("h2", style="margin: 0 0 15px 0; font-size: 20px;"))
                info_content.h2.string = f"📋 {item['title']}"

                info_details = soup.new_tag("div", style="display: flex; flex-wrap: wrap; gap: 15px;")

                details = [
                    ("📋 信息类型", item['info_type']),
                    ("📍 地区", item['area']),
                    ("📅 发布时间", item['pub_date']),
                    ("🔗 原始链接", f"<a href='{item['link']}' target='_blank' style='color: #ffeb3b;'>{item['link']}</a>"),
                    ("⏰ 抓取时间", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                ]

                for label, value in details:
                    detail_item = soup.new_tag("div", style="background: rgba(255,255,255,0.1); padding: 8px 12px; border-radius: 4px;")
                    if "原始链接" in label:
                        detail_item.append(BeautifulSoup(f"<strong>{label}:</strong> {value}", 'html.parser'))
                    else:
                        detail_item.string = f"{label}: {value}"
                    info_details.append(detail_item)

                info_content.append(info_details)
                info_header.append(info_content)
                soup.body.insert(0, info_header)

            # 保存文件
            file_path = save_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(str(soup))

            print(f"✅ 本地保存成功: {filename}")
            return file_path

        except Exception as e:
            print(f"❌ 保存项目详情页面失败: {e}")
            self.logger.error(f"保存项目详情页面失败: {e}")
            return None


def main():
    """主函数"""
    spider = ZhaobiaoSpider()
    return spider.run()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)