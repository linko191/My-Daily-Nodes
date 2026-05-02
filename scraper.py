
import asyncio
import aiohttp
import base64
import re
import sys
import urllib.parse
import random

# Source အသစ်များ (Vmess, Vless, Trojan အစုံပါဝင်သည်)
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

def is_target_country(config):
    """Vietnam, India, Turkey ဆိုင်ရာ စာသားပါ/မပါ စစ်ဆေးရန်"""
    if not config.strip() or "#" not in config:
        return False
    
    try:
        remark = urllib.parse.unquote(config.split("#", 1)[1])
        
        # နိုင်ငံအမည် အပြည့်အစုံ သို့မဟုတ် အလံပုံများကို စစ်ဆေးခြင်း (အကြီးအသေး မရွေးပါ)
        if re.search(r'(?i)(vietnam|india|turkey|🇻🇳|🇮🇳|🇹🇷)', remark):
            return True
            
        # နိုင်ငံကုဒ်များကို စစ်ဆေးခြင်း (အင်္ဂလိပ်စာလုံး 'in' နှင့် မမှားစေရန် အကြီးစာလုံး သီးသန့်စစ်သည်)
        if re.search(r'\b(VN|IN|TR)\b', remark):
            return True
    except:
        pass
    return False

async def main():
    connector = aiohttp.TCPConnector(limit=100)
    async with aiohttp.ClientSession(connector=connector) as session:
        print("--- Scraping Started... Looking for VN, IN, TR Nodes ---")
        all_raw_configs = []
        
        fetch_tasks = [fetch_configs(session, url) for url in SOURCES]
        results = await asyncio.gather(*fetch_tasks)
        
        for configs in results:
            all_raw_configs.extend(configs)

        print(f"Total found: {len(all_raw_configs)} nodes. Filtering strictly for VN, IN, TR...")

        # သတ်မှတ်ထားသော နိုင်ငံများ ဟုတ်မဟုတ် စစ်ထုတ်ခြင်း
        target_nodes = [cfg for cfg in all_raw_configs if is_target_country(cfg)]
        
        # ထပ်နေသော (Duplicate) လင့်ခ်များကို ဖယ်ရှားခြင်း
        target_nodes = list(set(target_nodes))

        # အလုံး ၃၀၀ ထက်များခဲ့လျှင် ၃၀၀ သာ ရွေးရန်
        if len(target_nodes) > 300:
            target_nodes = random.sample(target_nodes, 300)

        # File ထဲ သိမ်းခြင်း
        with open("True_IP_Configs.txt", "w", encoding="utf-8") as f:
            for node in target_nodes:
                f.write(node + "\n")
        
        print(f"--- Done! ---")
        print(f"Saved {len(target_nodes)} nodes from VN, IN, TR!")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(main())
