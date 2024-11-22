import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from wxauto import WeChat
import schedule
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
import os
import pythoncom

# Flask app setup
app = Flask(__name__)

# 目标网站URL
CHINA_DAILY_URL = 'https://www.chinadaily.com.cn/'
DECOHACK_URL = 'https://decohack.com/category/producthunt/'
GITHUB_TRENDING_URL = 'https://github.com/trending'

def fetch_links():
    """抓取包含当前日期的链接"""
    current_date = datetime.now().strftime('%m/%d')
    response = requests.get(CHINA_DAILY_URL)
    response.encoding = 'utf-8'  # 确保正确的编码，以防止中文乱码
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a', href=True)

    pattern = re.compile(re.escape(current_date))
    found_links = []

    for link in links:
        href = link['href']
        if not href.startswith('http'):
            href = requests.compat.urljoin(CHINA_DAILY_URL, href)

        if pattern.search(href):
            found_links.append(href)
            if len(found_links) == 5:  # 找到五个链接后停止搜索
                break

    return found_links

def fetch_latest_trending_decohack():
    """抓取Decohack最新的热榜数据"""
    try:
        response = requests.get(DECOHACK_URL, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        latest_trending = soup.find('h2')  # 找到第一个<h2>标签
        if latest_trending:
            title = latest_trending.get_text(strip=True)
            link = latest_trending.find('a')['href'] if latest_trending.find('a') else ''
            return {'title': title, 'link': link}
    except requests.RequestException as e:
        print(f"Error fetching Decohack data: {e}")
    return None

def fetch_latest_trending_github():
    """直接返回GitHub trending的链接"""
    return {'title': 'GitHub Trending', 'link': GITHUB_TRENDING_URL}

def format_trending_item(trending_item, source):
    """格式化热榜数据为文本格式"""
    if trending_item:
        text = f"# {source} Trending\n\n- {trending_item['title']}: {trending_item['link']}\n"
        return text
    return f"# {source} Trending\n\nNo trending items found."

def send_to_wechat(content):
    """发送内容到微信"""
    try:
        pythoncom.CoInitialize()  # 初始化COM库
        wx = WeChat()
        wx.SendMsg(content, '文件传输助手')  # 发送到文件传输助手
    except Exception as e:
        print(f"发送消息失败: {str(e)}")
    finally:
        pythoncom.CoUninitialize()  # 清理COM库

def job_daily_push():
    """定时任务：抓取并发送外刊和GitHub内容"""
    try:
        # 1. 抓取并发送外刊内容
        links = fetch_links()
        china_daily_content = "今日份外刊：\n" + "\n".join(f"{i + 1}. {link}" for i, link in enumerate(links)) if links else "今日份外刊：未找到链接。"
        send_to_wechat(china_daily_content)

        # 2. 抓取并发送GitHub内容
        decohack_item = fetch_latest_trending_decohack()
        github_item = fetch_latest_trending_github()
        trending_content = format_trending_item(decohack_item, "Decohack")
        trending_content += format_trending_item(github_item, "GitHub")
        send_to_wechat(trending_content)
        
    except Exception as e:
        print(f"推送任务执行失败: {str(e)}")

# 设置定时任务
scheduler = BackgroundScheduler()
scheduler.add_job(job_daily_push, 'cron', hour=23, minute=0)      # 晚上11点发送外刊和GitHub内容
scheduler.start()

@app.route('/')
def index():
    return "Server is running"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000) 