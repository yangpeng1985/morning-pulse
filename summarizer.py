"""
摘要生成器
目前仅支持 DeepSeek API
"""
import logging
import os
from typing import List

import httpx
from openai import OpenAI

from fetchers.base import Item


class Summarizer:
    def __init__(self, config: dict):
        self.api_key = config.get('api_key') or os.environ.get('DEEPSEEK_API_KEY', '')
        self.model = config.get('model', 'deepseek-chat')
        self.base_url = config.get('base_url', 'https://api.deepseek.com/v1')
        self.max_tokens = config.get('max_tokens', 300)
        self.temperature = config.get('temperature', 0.3)

        # 确保使用 DeepSeek Chat 模型
        if self.model == 'gpt-3.5-turbo' or not self.model:
            self.model = 'deepseek-chat'

        # 创建一个不经过任何代理的传输层，避免因环境变量中 SOCKS 代理导致 socksio 缺失错误
        transport = httpx.HTTPTransport(proxy=None)
        http_client = httpx.Client(transport=transport)
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            http_client=http_client
        )

    def summarize(self, items: List[Item]):
        """批量生成摘要，逐个调用 LLM"""
        for item in items:
            if not item.content_text:
                item.summary = '(无可用的文本内容)'
                continue
            try:
                item.summary = self._call_llm(item.content_text)
                logging.info(f"摘要生成成功: {item.title[:30]}...")
            except Exception as e:
                logging.error(f"为 {item.title} 生成摘要失败: {e}")
                item.summary = '(摘要生成失败)'

    def _call_llm(self, text: str) -> str:
        """调用 DeepSeek LLM 生成摘要"""
        prompt = f"请用中文为以下内容生成一段 100~300 字的摘要，要求简洁清晰：\n\n{text[:3000]}"
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个专业的文章摘要助手，只输出摘要内容。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        return response.choices[0].message.content.strip()
