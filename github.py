import time
import requests
from bs4 import BeautifulSoup
from wxauto import WeChat
import schedule

DECOHACK_URL = 'https://decohack.com/category/producthunt/'
GITHUB_TRENDING_URL = 'https://github.com/trending'


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
    wx = WeChat()
    wx.SendMsg(content, '文件传输助手')  # 发送到文件传输助手


def job():
    """定时任务：抓取并发送热榜内容"""
    decohack_item = fetch_latest_trending_decohack()
    github_item = fetch_latest_trending_github()

    text_content = format_trending_item(decohack_item, "Decohack")
    text_content += format_trending_item(github_item, "GitHub")

    send_to_wechat(text_content)


def main():
    # 设置每天7点执行任务
    schedule.every().day.at("23:03").do(job)
    print("Scheduler started, waiting for the next scheduled task...")

    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次任务


if __name__ == '__main__':
    main()