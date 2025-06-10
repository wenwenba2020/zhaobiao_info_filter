#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
招标信息爬虫启动脚本
基于个性化项目定制的完整爬虫系统

Author: Assistant
Date: 2025-06-09
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def check_environment():
    """检查运行环境"""
    print("🔧 检查运行环境...")
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("❌ Python版本过低，需要Python 3.7或更高版本")
        return False
    
    # 检查必要的库
    required_packages = [
        'selenium',
        'beautifulsoup4', 
        'requests',
        'webdriver_manager'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            if package == 'beautifulsoup4':
                try:
                    __import__('bs4')
                except ImportError:
                    missing_packages.append(package)
            elif package == 'webdriver_manager':
                try:
                    __import__('webdriver_manager')
                except ImportError:
                    missing_packages.append(package)
            else:
                missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("📦 请运行: pip install -r requirements.txt")
        return False
    
    print("✅ 环境检查通过")
    return True

def main():
    """主函数"""
    print("="*80)
    print("🚀 招标信息爬虫系统")
    print("="*80)
    print("📋 功能说明:")
    print("1. 自动检查系统环境")
    print("2. 引导用户登录")
    print("3. 自动进入会员中心")
    print("4. 处理个性化项目定制")
    print("5. 爬取并保存搜索结果")
    print("6. 自动上传到静态站点")
    print("="*80)
    
    # 环境检查
    if not check_environment():
        input("🔧 环境检查失败，按回车键退出...")
        return False
    
    try:
        # 导入并运行爬虫
        from zhaobiao_spider import ZhaobiaoSpider
        
        spider = ZhaobiaoSpider()
        success = spider.run()
        
        if success:
            print("\n🎉 爬虫执行成功！")
        else:
            print("\n❌ 爬虫执行失败，请检查日志文件")
        
        input("\n按回车键退出...")
        return success
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("📂 请确认src/zhaobiao_spider.py文件存在")
        input("按回车键退出...")
        return False
        
    except Exception as e:
        print(f"❌ 执行错误: {e}")
        input("按回车键退出...")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 