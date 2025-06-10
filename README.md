# 招标信息采集与过滤系统

一个用于自动化采集和过滤招标信息的Python工具。

## 功能特性

- 支持多关键词批量搜索
- 自动保存搜索结果页面
- 支持注释功能（使用#开头的行）
- 智能分类存储（按时间和关键词组织）
- 支持多种设备类型的信息采集：
  - 收单设备相关
  - 报销设备相关
  - 报账设备相关
  - IT和信息化相关

## 项目结构

```
zhaobiao_info_filter/
├── config/           # 配置文件目录
├── data/             # 数据存储目录
│   ├── attachments/  # 附件存储
│   ├── processed/    # 处理后的数据
│   ├── raw/         # 原始数据
│   ├── saved_pages/ # 保存的网页
│   └── scraped_pages/ # 爬取的页面
├── drivers/         # 浏览器驱动
├── logs/           # 日志文件
├── src/            # 源代码
│   └── utils/      # 工具函数
├── fix_chrome_driver.py  # Chrome驱动修复工具
├── requirements.txt      # 项目依赖
├── run_spider.py        # 爬虫运行入口
└── run_test.py         # 测试脚本
```

## 安装说明

1. 克隆仓库：
```bash
git clone https://github.com/wenwenba2020/zhaobiao_info_filter.git
cd zhaobiao_info_filter
```

2. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置Chrome驱动：
```bash
python fix_chrome_driver.py
```

## 使用说明

1. 准备关键词列表文件，每行一个关键词
2. 运行爬虫：
```bash
python run_spider.py
```

## 注意事项

- 确保系统已安装Chrome浏览器
- 需要稳定的网络连接
- 建议使用Python 3.8或更高版本

## 更新日志

### 2024.06.10
- 实现自动登录引导功能
- 完成会员中心自动导航
- 实现个性化项目定制页面的自动操作
- 支持自定义时间范围搜索
- 新增搜索结果页面的完整保存功能
- 添加FTP自动上传功能，支持静态站点访问
- 优化错误处理和日志记录

### 2024.06.09
- 初始版本发布
- 支持基本的招标信息采集功能
- 添加关键词分类功能

## 许可证

MIT License