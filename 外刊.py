import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from wxauto import WeChat
import schedule

# 目标网站URL
url = 'https://www.chinadaily.com.cn/'


def fetch_links():
    """抓取包含当前日期的链接"""
    current_date = datetime.now().strftime('%m/%d')
    response = requests.get(url)
    response.encoding = 'utf-8'  # 确保正确的编码，以防止中文乱码
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a', href=True)

    pattern = re.compile(re.escape(current_date))
    found_links = []

    for link in links:
        href = link['href']
        if not href.startswith('http'):
            href = requests.compat.urljoin(url, href)

        if pattern.search(href):
            found_links.append(href)
            if len(found_links) == 5:  # 找到五个链接后停止搜索
                break

    return found_links


def send_to_wechat(links):
    """发送链接到微信"""
    wx = WeChat()
    if links:
        message = "今日份外刊：\n" + "\n".join(f"{i + 1}. {link}" for i, link in enumerate(links))
    else:
        message = "今日份外刊：未找到链接。"

    wx.SendMsg(message, '文件传输助手')  # 发送到文件传输助手


def job():
    """定时任务：抓取并发送链接"""
    links = fetch_links()
    send_to_wechat(links)


def main():
    # 设置每天晚上10点执行任务
    schedule.every().day.at("23:00").do(job)
    print("Scheduler started, waiting for the next scheduled task...")

    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次任务


if __name__ == '__main__':
    main()
