"""
基础数据模型 Item
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Item:
    source_name: str
    title: str
    url: str
    publish_time: datetime
    content_text: str
    summary: Optional[str] = None
    item_id: str = ''
