"""
Bilibili UP 主视频抓取器
使用 bilibili-api-python 库 (pip install bilibili-api)
或者直接请求 Bilibili 开放 API（无需登录）
这里采用直接请求 API 的方式，更稳定
"""
import logging
import time
import hashlib
import urllib.parse
from typing import List
from datetime import datetime
from functools import lru_cache

import requests

from .base import Item

@lru_cache(maxsize=1)
def get_mixin_key() -> str:
    """获取 WBI 混合密钥，并缓存复用"""
    nav_url = "https://api.bilibili.com/x/web-interface/nav"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.bilibili.com/',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }
    resp = requests.get(nav_url, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if 'data' not in data or 'wbi_img' not in data.get('data', {}):
        raise RuntimeError("Bilibili nav 接口返回异常数据，缺少 wbi_img")
    wbi_img = data["data"]["wbi_img"]
    img_key = wbi_img["img_url"].rsplit("/", 1)[1].split(".")[0]
    sub_key = wbi_img["sub_url"].rsplit("/", 1)[1].split(".")[0]
    mixin = img_key + sub_key
    # B 站固定抽取顺序
    order = [46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45,
             35, 27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13]
    return ''.join(mixin[i] for i in order)[:32]

def sign_wbi(params: dict) -> dict:
    """为请求参数添加 w_rid 和 wts 签名，返回新字典"""
    mixin_key = get_mixin_key()
    params["wts"] = int(time.time())
    # 排序拼接
    sorted_params = sorted(params.items())
    query_str = urllib.parse.urlencode(sorted_params)
    sign = hashlib.md5((query_str + mixin_key).encode()).hexdigest()
    params["w_rid"] = sign
    return params

def fetch(source: dict) -> List[Item]:
    uid = source.get('uid')
    if not uid:
        raise ValueError("Bilibili 源必须提供 uid")

    cookie = source.get('cookie', '')          # 可选的 SESSDATA
    max_retries = source.get('max_retries', 3)
    logging.info(f"开始抓取 Bilibili UP主 {uid}")

    # 基础请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': f'https://space.bilibili.com/{uid}',
    }
    if cookie:
        headers['Cookie'] = f'SESSDATA={cookie};'
        logging.debug("使用登录态 Cookie 请求 Bilibili")

    # 带重试的请求
    for attempt in range(max_retries):
        try:
            params = {
                'mid': uid,
                'ps': 30,               # 获取最多 30 条，可根据需要调整
                'pn': 1,
            }
            sign_wbi(params)            # 注入 w_rid 和 wts

            # 增加常见浏览器请求头，降低风控概率
            req_headers = headers.copy()
            req_headers.setdefault('Accept', 'application/json, text/plain, */*')
            req_headers.setdefault('Accept-Language', 'zh-CN,zh;q=0.9')
            # 有些接口需要 Origin，否则会返回 412
            req_headers.setdefault('Origin', 'https://space.bilibili.com')
            req_headers.setdefault('Sec-Fetch-Site', 'same-site')
            req_headers.setdefault('Sec-Fetch-Mode', 'cors')
            req_headers.setdefault('Sec-Fetch-Dest', 'empty')

            resp = requests.get(
                'https://api.bilibili.com/x/space/wbi/arc/search',
                params=params,
                headers=req_headers,
                timeout=15
            )
            resp.raise_for_status()
            raw = resp.text
            try:
                data = resp.json()
            except ValueError:
                snippet = raw[:200] if raw else '(empty)'
                raise RuntimeError(f"B站API返回非JSON内容 (HTTP {resp.status_code}), 原始内容: {snippet}")

            code = data.get('code')
            if code == 0:
                break                    # 成功，跳出重试循环
            elif code in (-352, -412):   # 风控 / 请求过快
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Bilibili API 风控重试耗尽: {data.get('message', '')}")
                wait = (attempt + 1) * 2
                logging.warning(f"触发风控，{wait} 秒后重试...")
                time.sleep(wait)
                get_mixin_key.cache_clear()   # 强制刷新 WBI key
                continue
            else:
                raise RuntimeError(f"Bilibili API 返回错误: {data.get('message', '未知')}")
        except requests.exceptions.RequestException as exc:
            # 超时、连接错误、HTTP 412/502 等临时错误都进行重试
            if attempt == max_retries - 1:
                raise RuntimeError(f"Bilibili API 请求失败，已重试 {max_retries} 次: {exc}")
            wait = (attempt + 1) * 2
            logging.warning(f"请求异常（{exc}），{wait} 秒后重试...")
            time.sleep(wait)
            get_mixin_key.cache_clear()
            continue
    else:
        # 所有重试都用尽仍未成功
        raise RuntimeError("Bilibili API 抓取失败，重试耗尽")

    # 正常解析 vlist
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

    # ✅ 频率控制：休息一会再返回，避免连续请求风控
    time.sleep(1.5)
    logging.info(f"Bilibili 抓取完成，共 {len(items)} 条")
    return items
