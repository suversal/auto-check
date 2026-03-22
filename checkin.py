import requests
import json

# ================= 配置区 =================
USER = "xxx"
PASS = "xxx"
BASE_URL = "https://hdhive.com"

# 填入你刚才测试成功的 Token 和你的 ID
TG_TOKEN = "xxx"
TG_CHAT_ID = "xxx" # 请确保这个 ID 是正确的数字

# 本地测试记得开代理
PROXIES = {"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"}

LOGIN_ACTION_ID = "601d84138632d39f16adfce544ceb527a6f6243670"
CHECKIN_ACTION_ID = "409539c7faa0ad25d3e3e8c21465c10661896ca5a2"
# ==========================================

session = requests.Session()

def decode_next_response(response):
    """强制 UTF-8 解码并提取中文消息"""
    try:
        # 1. 强制使用 UTF-8 编码读取内容，解决乱码
        content = response.content.decode('utf-8')

        # 2. 寻找 JSON 行
        for line in content.split('\n'):
            if '{"error"' in line or '"success"' in line:
                start_idx = line.find('{')
                data = json.loads(line[start_idx:])
                if "error" in data:
                    err = data['error']
                    return f"{err.get('message', '错误')}: {err.get('description', '')}"
                return "✅ 签到操作成功"
    except Exception as e:
        print(f"[!] 解析异常: {e}")
    return "解析失败，请检查登录状态"

def send_tg_notice(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": f"🚀 <b>HDHive 签到任务</b>\n\n结果：{message}",
        "parse_mode": "HTML"
    }
    try:
        # 发送请求
        res = requests.post(url, json=payload, timeout=10, proxies=PROXIES)
        if res.status_code == 200:
            print("[+] Telegram 通知发送成功！")
        else:
            print(f"[!] TG 发送失败: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"[!] TG 连通异常: {e}")

def run_task():
    print("[*] 开始执行任务...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "Accept": "text/x-component",
        "Content-Type": "text/plain;charset=UTF-8",
    }

    try:
        # 1. 登录
        login_h = headers.copy()
        login_h["Next-Action"] = LOGIN_ACTION_ID
        session.post(f"{BASE_URL}/login", headers=login_h,
                     data=json.dumps([{"username": USER, "password": PASS}, "/"]),
                     allow_redirects=False)

        if 'token' not in session.cookies:
            print("[-] 登录失败")
            return

        # 2. 签到
        checkin_h = headers.copy()
        checkin_h["Next-Action"] = CHECKIN_ACTION_ID
        r_checkin = session.post(f"{BASE_URL}/", headers=checkin_h, data="[{},{}]")

        # 解析并通知
        final_msg = decode_next_response(r_checkin)
        print(f"[+] 最终反馈: {final_msg}")
        send_tg_notice(final_msg)

    except Exception as e:
        print(f"[-] 运行错误: {e}")

if __name__ == "__main__":
    run_task()