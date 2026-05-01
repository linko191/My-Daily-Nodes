import asyncio
import aiohttp
import base64
import re
import socket
import ipaddress
import sys
import random

# နေ့စဉ် Update ဖြစ်နေမယ့် V2ray/Vless Source အသစ်များ
SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/normal/vless",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub.txt",
    "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2"
]

# တရားဝင် Cloudflare IPv4 Ranges များ (ပိုမိုတိကျစေရန်)
CLOUDFLARE_IPV4_RANGES = [
    "173.245.0.0/20", "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22",
    "141.101.64.0/18", "108.162.192.0/18", "190.93.240.0/20", "188.114.96.0/20",
    "197.234.240.0/22", "198.41.128.0/17", "162.158.0.0/15", "104.16.0.0/13",
    "104.24.0.0/14", "172.64.0.0/13", "131.0.72.0/22"
]
cf_networks = [ipaddress.ip_network(ip) for ip in CLOUDFLARE_IPV4_RANGES]

def is_cloudflare(ip_str):
    """IP သည် Cloudflare Range ထဲတွင် ပါဝင်ခြင်း ရှိ/မရှိ စစ်ဆေးရန်"""
    try:
        ip = ipaddress.ip_address(ip_str)
        for net in cf_networks:
            if ip in net:
                return True
        return False
    except ValueError:
        return False

def fix_base64_padding(data):
    """Base64 decode လုပ်ရာတွင် Error မတက်စေရန် Padding ဖြည့်ပေးခြင်း"""
    missing_padding = len(data) % 4
    if missing_padding:
        data += '=' * (4 - missing_padding)
    return data

async def fetch_configs(session, url):
    """URL မှ Config များကို ယူရန်"""
    try:
        async with session.get(url, timeout=15) as response:
            text = await response.text()
            try:
                # Base64 decode လုပ်ခြင်း
                padded_text = fix_base64_padding(text.strip())
                decoded_data = base64.b64decode(padded_text).decode('utf-8')
                return decoded_data.splitlines()
            except Exception:
                # Base64 မဟုတ်ခဲ့လျှင် ရိုးရိုး Text အတိုင်းယူရန်
                return text.splitlines()
    except Exception as e:
        print(f"[!] Error fetching {url}: {e}")
        return []

async def check_ip_and_filter(config):
    """Config ထဲမှ Host ကိုရှာပြီး Cloudflare ဟုတ်မဟုတ် စစ်ဆေးရန်"""
    if not config.strip():
        return None

    # vless:// သို့မဟုတ် trojan:// ပုံစံများမှ user@host:port ကို ရှာခြင်း
    pattern = r"@(.*?):(\d+)"
    match = re.search(pattern, config)
    
    if match:
        host = match.group(1)
        
        # IP Address အစစ် (ဥပမာ - 192.168.1.1) ဖြစ်နေလျှင် တိုက်ရိုက်စစ်ရန်
        try:
            if not is_cloudflare(host):
                return config
            return None
        except ValueError:
            pass # IP အစစ်မဟုတ်ဘဲ Domain ဖြစ်နေလျှင် ဆက်သွားရန်

        try:
            # Domain ကို IP အဖြစ်ပြောင်းခြင်း (Async ပုံစံဖြင့်)
            loop = asyncio.get_running_loop()
            # socket.AF_INET ကိုသုံးပြီး IPv4 ကိုသာ ယူရန်
            info = await loop.getaddrinfo(host, None, family=socket.AF_INET)
            ip = info[0][4][0]
            
            # Cloudflare မဟုတ်မှသာ လက်ခံမည်
            if not is_cloudflare(ip):
                return config
        except Exception:
            return None
            
    return None

async def main():
    # TCP Connector limit ကိုတိုးပေးထားခြင်းဖြင့် မြန်နှုန်းပိုကောင်းစေရန်
    connector = aiohttp.TCPConnector(limit=100)
    async with aiohttp.ClientSession(connector=connector) as session:
        print("--- Scraping Started... Please wait ---")
        all_raw_configs = []
        
        # URLs များမှ Data များကို တပြိုင်နက်တည်း ယူရန်
        fetch_tasks = [fetch_configs(session, url) for url in SOURCES]
        results = await asyncio.gather(*fetch_tasks)
        
        for configs in results:
            all_raw_configs.extend(configs)

        print(f"Total found: {len(all_raw_configs)} nodes.")
        print("Filtering True-IP nodes... (This might take a minute depending on the node count)")

        # Multi-threading (Async Tasks) နဲ့ IP တွေလိုက်စစ်ခြင်း
        tasks = [check_ip_and_filter(cfg) for cfg in all_raw_configs]
        filtered_results = await asyncio.gather(*tasks)

        # Null မဟုတ်တဲ့ (Cloudflare မဟုတ်တဲ့) ဟာတွေကိုပဲ ယူမယ်
        true_ip_nodes = [res for res in filtered_results if res]

        # Node တွေများလွန်းရင် ဖုန်းလေးတဲ့အတွက် Random အခု ၁၅၀ သာ ယူရန်
        if len(true_ip_nodes) > 150:
            true_ip_nodes = random.sample(true_ip_nodes, 150)

        # File ထဲ သိမ်းခြင်း
        with open("True_IP_Configs.txt", "w", encoding="utf-8") as f:
            for node in true_ip_nodes:
                f.write(node + "\n")
        
        print(f"--- Done! ---")
        print(f"Saved {len(true_ip_nodes)} True-IP nodes to 'True_IP_Configs.txt'")

if __name__ == "__main__":
    # Windows မှာ Asyncio Error တက်တတ်တာကို ဖြေရှင်းရန်
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(main())
