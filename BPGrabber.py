import requests
import json
import re
import argparse
import sys
from datetime import datetime

# Discord Token
TOKEN = "YourToken"
Messagecount = 2500
# 关键词
DEFAULT_KEYWORDS = []

# Discord频道配置
DISCORD_CHANNELS = {
    "sfs_official": {
        "name": "Spaceflight Simulator",
        "guild_id": "400050897700257792",
        "channel_id": "993056668118163466"
    }
}

def get_discord_messages(channel_id, limit=100, before=None):
    """获取Discord频道消息 - 单次请求，最多100条"""
    headers = {
        'Authorization': TOKEN,
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    url = f'https://discord.com/api/v9/channels/{channel_id}/messages'
    # Discord API限制单次请求最多100条消息
    params = {'limit': min(limit, 100)}
    if before:
        params['before'] = before
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return []

def extract_sharing_links(text):
    """提取sharing链接"""
    pattern = r'https://sharing\.spaceflightsimulator\.app/[^\s<>"]+'
    return re.findall(pattern, text)

def format_timestamp(timestamp_str):
    """格式化时间戳"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp_str

def search_channel(channel_key, keywords=None, limit=1000):
    """搜索单个频道"""
    if channel_key not in DISCORD_CHANNELS:
        print(f"未知频道: {channel_key}")
        return []
    
    channel_info = DISCORD_CHANNELS[channel_key]
    channel_id = channel_info["channel_id"]
    channel_name = channel_info["name"]
    
    print(f"搜索频道: {channel_name}")
    print(f"频道ID: {channel_id}")
    
    all_messages = []
    before_id = None
    batch_size = 100  # Discord API限制单次最多100条
    
    # 获取消息 - 多次请求直到达到目标数量
    while len(all_messages) < limit:
        remaining = limit - len(all_messages)
        current_batch_size = min(batch_size, remaining)
        
        print(f"正在获取消息... 已获取: {len(all_messages)}, 目标: {limit}")
        messages = get_discord_messages(channel_id, current_batch_size, before_id)
        
        if not messages:
            print("没有更多消息了")
            break
            
        all_messages.extend(messages)
        before_id = messages[-1]["id"]
        
        # 如果返回的消息少于请求的数量，说明已经到达频道末尾
        if len(messages) < current_batch_size:
            print("已到达频道末尾")
            break
    
    print(f"获取到 {len(all_messages)} 条消息")
    
    # 处理消息
    results = []
    for message in all_messages:
        content = message.get('content', '')
        sharing_links = extract_sharing_links(content)


        if not sharing_links:
            continue
        
        # 关键词匹配
        if keywords:
            content_lower = content.lower()
            if not any(kw.lower() in content_lower for kw in keywords):
                continue
        
        # 解析消息
        author = message.get('author', {})
        timestamp = format_timestamp(message.get('timestamp', ''))
        
        result = {
            "author": author.get('username', 'Unknown'),
            "link": sharing_links[0] if sharing_links else "",
            "channel": channel_name,
            "timestamp": timestamp,
            "content": content
        }
        
        results.append(result)
        print(f"找到蓝图: {author.get('username', 'Unknown')}")
    
    print(f"频道 {channel_name}: 找到 {len(results)} 个蓝图")
    return results

def main():
    print("Discord蓝图搜索器")
    
    # 搜索所有频道
    all_results = []
    
    for channel_key in DISCORD_CHANNELS.keys():
        results = search_channel(channel_key, keywords=None, limit=Messagecount)
        all_results.extend(results)
    
    print(f"\n总共找到 {len(all_results)} 个蓝图")
    print("正在保存到 BPLinks.txt...")
    
    # 保存到txt文件
    with open('BPLinks.txt', 'w', encoding='utf-8') as f:
        for result in all_results:
            author = result['author']
            content = result['content'].replace('\n', ' ').replace('\r', ' ')  # 移除换行符
            link = result['link']
            
            f.write(f"{author} {link}\n")
    
    print(f"已保存 {len(all_results)} 个蓝图")
if __name__ == "__main__":
    main()