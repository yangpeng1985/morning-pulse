#!/usr/bin/python3
"""
每日订阅摘要 - 主调度器
"""
import argparse
import logging
import sys
import subprocess
from pathlib import Path
from datetime import datetime

import yaml

from fetchers import rss_fetcher, youtube_fetcher, bilibili_fetcher
from summarizer import Summarizer
from reporter import Reporter
from state import StateStore
from utils import setup_logging, get_today_str

FETCHER_MAP = {
    'rss': rss_fetcher.fetch,
    'youtube': youtube_fetcher.fetch,
    'bilibili': bilibili_fetcher.fetch,
}

def load_config(config_path: str) -> dict:
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def run(config_path: str, test_mode: bool = False, source_types=None):
    config = load_config(config_path)
    setup_logging(level=config.get('logging_level', 'INFO'))

    logging.info("开始执行每日订阅摘要")
    if test_mode:
        logging.info("测试模式：将忽略已有状态，重新获取所有内容。")

    # 初始化状态存储
    state_db_path = Path(config.get('state_db_path', 'state.db'))
    state = StateStore(str(state_db_path))

    # 初始化摘要生成器
    summarizer = Summarizer(config.get('llm', {}))

    # 收集所有新 item
    all_new_items = []
    sources = config.get('sources', [])
    if source_types:
        original_count = len(sources)
        sources = [s for s in sources if s.get('type', '').lower() in source_types]
        logging.info(f"来源类型过滤：从 {original_count} 个源中选出 {len(sources)} 个")

    for source in sources:
        source_type = source.get('type', '').lower()
        if source_type not in FETCHER_MAP:
            logging.warning(f"未知的订阅类型: {source_type}，跳过")
            continue

        fetcher_func = FETCHER_MAP[source_type]
        try:
            items = fetcher_func(source)
        except Exception as e:
            logging.error(f"抓取 {source.get('name', source_type)} 失败: {e}")
            continue

        # 过滤已处理的 item（测试模式下不检查状态）
        if test_mode:
            new_items = items
        else:
            new_items = [it for it in items if not state.has_seen(it.item_id)]
        logging.info(f"{source.get('name', source_type)}: 获取 {len(items)} 条，新增 {len(new_items)} 条")

        # 为每个 item 保存源名称
        for it in new_items:
            it.source_name = source.get('name', source_type)
        all_new_items.extend(new_items)

    if not all_new_items:
        logging.info("没有新的节目，跳过摘要生成和报告输出")
        state.close()
        return

    # 生成摘要
    logging.info(f"开始为 {len(all_new_items)} 条节目生成摘要")
    summarizer.summarize(all_new_items)

    # 将已处理的 item 标记为已见（测试模式下不记录）
    if not test_mode:
        for it in all_new_items:
            state.mark_seen(it.item_id, it.publish_time)

    # 生成报告
    output_dir = Path(config.get('output_dir', 'output'))
    output_dir.mkdir(parents=True, exist_ok=True)
    today = get_today_str()
    report_filename = f"{today}.md"
    report_path = output_dir / report_filename

    reporter = Reporter(config.get('report', {}))
    reporter.render(all_new_items, str(report_path))
    logging.info(f"报告已保存至 {report_path}")

    # 执行后置自定义命令 / 默认用 Typora 打开报告
    post_command = config.get('post_command')
    if not post_command:
        post_command = 'open -a Typora {file}'
    cmd = post_command.replace('{file}', str(report_path))
    try:
        logging.info(f"执行后置命令: {cmd}")
        subprocess.run(cmd, shell=True)
    except Exception as e:
        logging.error(f"后置命令执行失败: {e}")

    # 可选邮件发送
    email_config = config.get('email', None)
    if email_config and email_config.get('enabled', False):
        try:
            reporter.send_email(email_config, all_new_items, today)
            logging.info("邮件发送成功")
        except Exception as e:
            logging.error(f"邮件发送失败: {e}")

    state.close()
    logging.info("每日订阅摘要执行完毕")

def main():
    parser = argparse.ArgumentParser(description='每日订阅摘要')
    parser.add_argument('--config', default='config.yaml', help='配置文件路径')
    parser.add_argument('--test', action='store_true', help='测试模式，忽略状态记录，每次均获取所有内容')
    parser.add_argument('--source-type', action='append', dest='source_types',
                        help='只抓取指定类型的源，可重复使用。例如 --source-type rss --source-type bilibili')
    args = parser.parse_args()
    run(args.config, test_mode=args.test, source_types=args.source_types)

if __name__ == '__main__':
    main()
