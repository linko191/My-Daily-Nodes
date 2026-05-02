import asyncio
import aiohttp
import base64
import re
import sys
import urllib.parse
import random

# Source အသစ်များ (Vmess နဲ့ Trojan တွေပါ ထပ်တိုးထားပါတယ်)
SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/normal/vless",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/normal/vmess",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/normal/trojan",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub.txt",
    "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2"
]

def fix_base64_padding(data):
    missing_padding = len(data) % 4
    if missing_padding:
        data += '=' * (4 - missing_padding)
    return data

async def fetch_configs(session, url):
    try:
        async with session.get(url, timeout=15) as response:
            text = await response.text()
            try:
                padded_text = fix_base64_padding(text.strip())
                decoded_data = base64.b64decode(padded_text).decode('utf-8')
                return decoded_data.splitlines()
            except Exception:
                return text.splitlines()
    except Exception as e:
        print(f"[!] Error fetching {url}: {e}")
        return []

def is_argentina(config):
    """Node အမည်တွင် Argentina ဆိုင်ရာ စာသားပါ/မပါ စစ်ဆေးရန်"""
    if not config.strip() or "#" not in config:
        return False
    
    # URL encoded ဖြစ်နေသော နာမည်များကို ဖတ်နိုင်ရန် ပြောင်းခြင်း
    try:
        remark = urllib.parse.unquote(config.split("#", 1)[1])
        # "argentina", "🇦🇷", သို့မဟုတ် "AR" (Case-insensitive) ကို ရှာခြင်း
        if re.search(r'(?i)(argentina|🇦🇷|\bar\b)', remark):
            return True
    except:
        pass
    return False

async def main():
    connector = aiohttp.TCPConnector(limit=100)
    async with aiohttp.ClientSession(connector=connector) as session:
        print("--- Scraping Started... Looking for Argentina (AR) Nodes ---")
        all_raw_configs = []
        
        fetch_tasks = [fetch_configs(session, url) for url in SOURCES]
        results = await asyncio.gather(*fetch_tasks)
        
        for configs in results:
            all_raw_configs.extend(configs)

        print(f"Total found: {len(all_raw_configs)} nodes. Filtering strictly for AR...")

        # Argentina ဟုတ်မဟုတ် စစ်ထုတ်ခြင်း
        ar_nodes = [cfg for cfg in all_raw_configs if is_argentina(cfg)]
        
        # ထပ်နေသော (Duplicate) လင့်ခ်များကို ဖယ်ရှားခြင်း
        ar_nodes = list(set(ar_nodes))

        # အလုံး ၃၀၀ ထက်များခဲ့လျှင် ၃၀၀ သာ ရွေးရန်
        if len(ar_nodes) > 300:
            ar_nodes = random.sample(ar_nodes, 300)

        # File ထဲ သိမ်းခြင်း
        with open("True_IP_Configs.txt", "w", encoding="utf-8") as f:
            for node in ar_nodes:
                f.write(node + "\n")
        
        print(f"--- Done! ---")
        print(f"Saved {len(ar_nodes)} Argentina nodes!")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(main())
