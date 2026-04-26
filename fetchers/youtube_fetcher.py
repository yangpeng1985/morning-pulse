"""
YouTube 频道抓取器
使用 yt-dlp 或 YouTube Data API v3（这里实现基于 yt-dlp，通过 subprocess 调用）
注意：需要预先安装 yt-dlp 库 (pip install yt-dlp)
"""
import json
import logging
import subprocess
from typing import List
from datetime import datetime

from .base import Item

def fetch(source: dict) -> List[Item]:
    channel_url = source.get('url')
    max_results = source.get('max_results', 10)

    if not channel_url:
        raise ValueError("YouTube 源必须提供 url")

    logging.info(f"开始抓取 YouTube: {channel_url}")

    # 使用 yt-dlp 获取最新的视频信息 (JSON 输出)
    cmd = [
        'yt-dlp', '--flat-playlist', '--dump-json', '--no-download',
        '--playlist-end', str(max_results), channel_url
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise RuntimeError(f"yt-dlp 错误: {result.stderr}")
    except FileNotFoundError:
        logging.error("yt-dlp 未安装，请运行 pip install yt-dlp")
        return []

    items = []
    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        title = data.get('title', '无标题')
        webpage_url = data.get('webpage_url', '')
        timestamp = data.get('timestamp')
        pub_time = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
        # 对于视频，content_text 可使用 description
        description = data.get('description', '')
        item_id = data.get('id', webpage_url)

        item = Item(
            source_name='',
            title=title,
            url=webpage_url,
            publish_time=pub_time,
            content_text=description,
            item_id=item_id
        )
        items.append(item)

    logging.info(f"YouTube 抓取完成，共 {len(items)} 条")
    return items
