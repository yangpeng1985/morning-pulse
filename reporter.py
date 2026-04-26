"""
报告生成器
支持 Markdown 格式输出，以及可选邮件发送
"""
import logging
from typing import List
from pathlib import Path
from datetime import datetime

from fetchers.base import Item

class Reporter:
    def __init__(self, config: dict):
        self.config = config

    def render(self, items: List[Item], output_path: str):
        """生成 Markdown 报告并写入文件"""
        lines = []
        lines.append("# 每日订阅摘要\n")
        lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        lines.append("---\n")

        # 按来源分组
        sources = {}
        for item in items:
            src = item.source_name
            sources.setdefault(src, []).append(item)

        for src, src_items in sources.items():
            lines.append(f"## {src}\n")
            for it in src_items:
                lines.append(f"### [{it.title}]({it.url})\n")
                lines.append(f"- **发布时间**: {it.publish_time.strftime('%Y-%m-%d %H:%M')}")
                lines.append(f"- **摘要**: {it.summary or '(无摘要)'}\n")
            lines.append("---\n")

        content = '\n'.join(lines)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logging.info(f"报告已写入 {output_path}")

    def send_email(self, email_config: dict, items: List[Item], date_str: str):
        """发送邮件（简化版，使用 smtplib）"""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        # 构建 HTML 内容（简单起见，仅文本）
        body_parts = [f"每日订阅摘要 - {date_str}"]
        for item in items:
            body_parts.append(f"\n• {item.title}\n  {item.summary}\n  {item.url}")
        body = '\n'.join(body_parts)

        msg = MIMEMultipart()
        msg['From'] = email_config['from']
        msg['To'] = email_config['to']
        msg['Subject'] = f"每日订阅摘要 - {date_str}"
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        with smtplib.SMTP_SSL(email_config['smtp_host'], email_config['smtp_port']) as server:
            server.login(email_config['username'], email_config['password'])
            server.send_message(msg)
