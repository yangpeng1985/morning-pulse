"""
RSS 订阅源抓取器
使用 feedparser 解析 RSS/Atom
"""
import logging
from typing import List
from datetime import datetime
import feedparser

from .base import Item

def fetch(source: dict) -> List[Item]:
    url = source.get('url')
    if not url:
        raise ValueError("RSS 源必须提供 url")

    logging.info(f"开始抓取 RSS: {url}")
    feed = feedparser.parse(url)

    items = []
    for entry in feed.entries[:10]:  # 限制前 10 条
        title = entry.get('title', '无标题')
        link = entry.get('link', '')
        published = entry.get('published_parsed') or entry.get('updated_parsed')
        pub_time = None
        if published:
            pub_time = datetime(*published[:6])
        else:
            pub_time = datetime.now()

        # 获取内容文本（description 或者 content）
        content = ''
        if 'content' in entry and entry.content:
            content = entry.content[0].get('value', '')
        elif 'summary' in entry:
            content = entry.summary
        else:
            content = ''  # 可能无法获取

        item = Item(
            source_name='',  # 由主调度器填充
            title=title,
            url=link,
            publish_time=pub_time,
            content_text=content,
            item_id=link  # 以链接作为唯一标识
        )
        items.append(item)

    logging.info(f"RSS 抓取完成，共 {len(items)} 条")
    return items
