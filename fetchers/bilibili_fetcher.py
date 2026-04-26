"""
Bilibili UP 主视频抓取器
使用 bilibili-api-python 库 (pip install bilibili-api)
或者直接请求 Bilibili 开放 API（无需登录）
这里采用直接请求 API 的方式，更稳定
"""
import logging
from typing import List
from datetime import datetime
import requests

from .base import Item

def fetch(source: dict) -> List[Item]:
    uid = source.get('uid')
    if not uid:
        raise ValueError("Bilibili 源必须提供 uid")

    logging.info(f"开始抓取 Bilibili UP主 {uid}")

    # B 站 API: 获取用户最近投稿
    url = f"https://api.bilibili.com/x/space/arc/search?mid={uid}&ps=10&pn=1"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://space.bilibili.com/'
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise RuntimeError(f"请求 Bilibili API 失败: {e}")

    if data.get('code') != 0:
        raise RuntimeError(f"Bilibili API 返回错误: {data.get('message', '未知')}")

    vlist = data['data']['list']['vlist']
    items = []
    for v in vlist:
        title = v.get('title', '无标题')
        aid = v.get('aid')
        bvid = v.get('bvid', '')
        link = f"https://www.bilibili.com/video/{bvid}" if bvid else f"https://www.bilibili.com/video/av{aid}"
        created = v.get('created')
        pub_time = datetime.fromtimestamp(created) if created else datetime.now()
        description = v.get('description', '')

        item_id = str(aid) if aid else link

        item = Item(
            source_name='',
            title=title,
            url=link,
            publish_time=pub_time,
            content_text=description,
            item_id=item_id
        )
        items.append(item)

    logging.info(f"Bilibili 抓取完成，共 {len(items)} 条")
    return items
