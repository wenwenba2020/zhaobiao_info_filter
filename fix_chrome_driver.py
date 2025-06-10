#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChromeDriver问题修复脚本
解决Chrome驱动版本不匹配的问题
"""

import os
import sys
import subprocess
import winreg
import requests
import zipfile
from pathlib import Path

def get_chrome_version():
    """获取Chrome浏览器版本"""
    print("🔍 检测Chrome版本...")
    
    try:
        # 方法1: 通过注册表
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
            version = winreg.QueryValueEx(key, "version")[0]
            winreg.CloseKey(key)
            print(f"✅ 检测到Chrome版本: {version}")
            return version
        except:
            pass
        
        # 方法2: 通过程序文件
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
        ]
        
        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                try:
                    result = subprocess.run([chrome_path, "--version"], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        version = result.stdout.strip().split()[-1]
                        print(f"✅ 检测到Chrome版本: {version}")
                        return version
                except:
                    continue
        
        print("❌ 无法检测Chrome版本")
        return None
        
    except Exception as e:
        print(f"❌ Chrome版本检测失败: {e}")
        return None

def get_chromedriver_download_url(chrome_version):
    """获取对应版本的ChromeDriver下载链接"""
    if not chrome_version:
        return None
    
    major_version = chrome_version.split('.')[0]
    
    try:
        # Chrome 115+使用新的下载地址
        if int(major_version) >= 115:
            # 查询可用版本
            api_url = f"https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                versions = data.get('versions', [])
                
                # 查找匹配的版本
                for version_data in reversed(versions):
                    if version_data['version'].startswith(major_version + '.'):
                        downloads = version_data.get('downloads', {})
                        chromedriver_downloads = downloads.get('chromedriver', [])
                        
                        for download in chromedriver_downloads:
                            if download.get('platform') == 'win64':
                                return download.get('url')
            
            # 备用链接
            return f"https://storage.googleapis.com/chrome-for-testing-public/{chrome_version}/win64/chromedriver-win64.zip"
        else:
            # 旧版本Chrome
            return f"https://chromedriver.storage.googleapis.com/{chrome_version}/chromedriver_win32.zip"
    
    except Exception as e:
        print(f"⚠️  获取下载链接失败: {e}")
        return None

def download_chromedriver(download_url, save_path):
    """下载ChromeDriver"""
    try:
        print(f"📥 正在下载ChromeDriver...")
        print(f"下载地址: {download_url}")
        
        response = requests.get(download_url, timeout=30)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ 下载完成: {save_path}")
            return True
        else:
            print(f"❌ 下载失败，状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return False

def extract_chromedriver(zip_path, extract_dir):
    """解压ChromeDriver"""
    try:
        print("📦 正在解压ChromeDriver...")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # 查找chromedriver.exe文件
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file == 'chromedriver.exe':
                    source_path = os.path.join(root, file)
                    dest_path = extract_dir / "chromedriver.exe"
                    
                    # 移动到目标位置
                    if source_path != str(dest_path):
                        os.rename(source_path, dest_path)
                    
                    print(f"✅ 解压完成: {dest_path}")
                    return str(dest_path)
        
        print("❌ 解压后未找到chromedriver.exe")
        return None
        
    except Exception as e:
        print(f"❌ 解压失败: {e}")
        return None

def fix_chromedriver():
    """修复ChromeDriver问题"""
    print("="*60)
    print("🛠️  ChromeDriver问题修复工具")
    print("="*60)
    
    # 1. 检测Chrome版本
    chrome_version = get_chrome_version()
    if not chrome_version:
        print("\n❌ 无法检测Chrome版本，请确保已安装Chrome浏览器")
        print("下载地址: https://www.google.com/chrome/")
        return False
    
    # 2. 创建drivers目录
    drivers_dir = Path("drivers")
    drivers_dir.mkdir(exist_ok=True)
    
    # 3. 检查是否已有ChromeDriver
    chromedriver_path = drivers_dir / "chromedriver.exe"
    if chromedriver_path.exists():
        print(f"\n⚠️  发现已存在的ChromeDriver: {chromedriver_path}")
        replace = input("是否替换为新版本？(y/N): ").lower().strip()
        if replace not in ['y', 'yes', '是']:
            print("保持现有版本")
            return True
        else:
            chromedriver_path.unlink()  # 删除旧版本
    
    # 4. 获取下载链接
    print(f"\n🔍 获取Chrome {chrome_version}对应的ChromeDriver...")
    download_url = get_chromedriver_download_url(chrome_version)
    
    if not download_url:
        print("\n❌ 无法获取下载链接，请手动下载:")
        print("1. 访问: https://chromedriver.chromium.org/downloads")
        print("2. 下载对应版本的ChromeDriver")
        print(f"3. 解压到: {chromedriver_path.absolute()}")
        return False
    
    # 5. 下载ChromeDriver
    zip_path = drivers_dir / "chromedriver.zip"
    if not download_chromedriver(download_url, zip_path):
        return False
    
    # 6. 解压ChromeDriver
    final_path = extract_chromedriver(zip_path, drivers_dir)
    if not final_path:
        return False
    
    # 7. 清理临时文件
    try:
        zip_path.unlink()
        # 清理解压产生的多余目录
        for item in drivers_dir.iterdir():
            if item.is_dir():
                import shutil
                shutil.rmtree(item)
    except:
        pass
    
    print(f"\n🎉 ChromeDriver安装成功！")
    print(f"路径: {final_path}")
    
    return True

def main():
    """主函数"""
    try:
        success = fix_chromedriver()
        
        if success:
            print("\n✅ ChromeDriver修复完成！")
            print("现在可以运行测试脚本了:")
            print("python src/test_spider.py")
        else:
            print("\n❌ ChromeDriver修复失败")
            print("请手动下载并配置ChromeDriver")
        
        input("\n按回车键退出...")
        
    except KeyboardInterrupt:
        print("\n⏹️  用户中断")
    except Exception as e:
        print(f"\n💥 程序错误: {e}")

if __name__ == "__main__":
    main() 