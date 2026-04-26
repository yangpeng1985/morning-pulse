"""
通用工具函数
"""
import logging
import sys
from datetime import date

def setup_logging(level: str = 'INFO'):
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )

def get_today_str() -> str:
    return date.today().isoformat()
