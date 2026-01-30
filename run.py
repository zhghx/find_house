import asyncio
import time
import json
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

from notify import send_wechat

# 配置参数
TARGET_URL = "https://www.ur-net.go.jp/chintai/kanto/kanagawa/40_1750.html"
LOG_FILE = "ur_stock.log"

async def monitor_ur():
    # 1. 更新 Schema 配置
    schema = {
        "name": "UR Room Detailed List",
        "baseSelector": "tr.js-log-item", 
        "fields": [
            {"name": "room_id", "selector": "td.rep_room-name", "type": "text"},    # 房号
            {"name": "type", "selector": "td.rep_room-type", "type": "text"},       # 户型
            {"name": "area", "selector": "td.rep_room-floor", "type": "text"},      # 面积
            {"name": "floor_info", "selector": "td.rep_room-kai", "type": "text"},  # 楼层
            # 根据图片，租金在 span class="item_price rep_room-price" 中
            {"name": "rent", "selector": "span.rep_room-price", "type": "text"},
            # (可选) 如果你还需要共益费，可以取消下面这行的注释
            # {"name": "fee", "selector": "span.rep_room-commonfee", "type": "text"} 
        ],
    }
    
    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=False)

    browser_cfg = BrowserConfig(
        headless=True, 
        enable_stealth=True,
        browser_type="chromium"
    )

    run_cfg = CrawlerRunConfig(
        # 1. 【修改点】不要等具体的房源行，改为等页面标题或 body
        # 这样无论有房没房，只要页面打开了就会继续
        wait_for="css:body", 
        
        # 2. 【新增点】给 JS 一点时间加载数据
        # 即使没房，等2-3秒也能确保不是因为网速慢导致的误判
        delay_before_return_html=3.0,

        extraction_strategy=extraction_strategy,
        cache_mode="bypass"
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(url=TARGET_URL, config=run_cfg)
        
        if result.success and result.extracted_content:
            rooms = json.loads(result.extracted_content)
            
            # 过滤掉空行
            valid_rooms = [r for r in rooms if r.get("room_id")]
            
            if valid_rooms:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n[{timestamp}] 📢 发现 {len(valid_rooms)} 个可用房源：")
                print("=" * 80) #稍微拉长分割线
                
                result_entry = f"[{timestamp}] 检测到房源: \n------\n"
                for room in valid_rooms:
                    # ▼▼▼ 在输出中加入租金 ▼▼▼
                    rent_price = room.get('rent', '未知').strip()
                    
                    output = (f"房号: {room['room_id'].strip()} | "
                              f"租金: {rent_price} | "  # 新增显示
                              f"户型: {room['type'].strip()} | "
                              f"面积: {room['area'].strip()} | "
                              f"楼层: {room['floor_info'].strip()}")
                    print(output)
                    
                    # 记录日志也加上价格
                    result_entry += f" {output}\n------\n"
                
                # 写入日志
                # with open(LOG_FILE, "a", encoding="utf-8") as f:
                #     f.write(result_entry + "\n")
                # print("=" * 80)
                
                # ▼▼▼ 4. 发送微信推送 ▼▼▼
                print("正在推送微信通知...")
                send_wechat(result_entry)
                
            else:
                print(f"[{time.strftime('%H:%M:%S')}] 页面已加载，但未发现具体房源行。")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] 目前无房（未找到 tr.js-log-item）。")

if __name__ == "__main__":
    asyncio.run(monitor_ur())
