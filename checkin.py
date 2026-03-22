import os
import requests
import json
import time

# 从 GitHub Secrets 读取环境变量
ACCOUNTS_JSON = os.getenv("HD_ACCOUNTS", "[]")
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

BASE_URL = "https://hdhive.com"
LOGIN_ACTION_ID = "601d84138632d39f16adfce544ceb527a6f6243670"
CHECKIN_ACTION_ID = "409539c7faa0ad25d3e3e8c21465c10661896ca5a2"

def decode_next_response(response):
    try:
        # 强制 UTF-8 解码解决乱码
        text = response.content.decode('utf-8')
        for line in text.split('\n'):
            if '{"response"' in line or '{"error"' in line:
                json_data = json.loads(line[line.find('{'):])
                if "response" in json_data:
                    return f"✅ {json_data['response'].get('message', '成功')}"
                if "error" in json_data:
                    return f"❌ {json_data['error'].get('description', '失败')}"
    except:
        pass
    return "❓ 解析异常"

def send_tg_notice(summary):
    if not TG_TOKEN or not TG_CHAT_ID: return
    text = "🚀 <b>HDHive 签到汇总</b>\n" + "------------------------\n" + "\n".join(summary)
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML"})

def run():
    try:
        accounts = json.loads(ACCOUNTS_JSON)
    except:
        print("账号 JSON 格式错误"); return

    summary = []
    for acc in accounts:
        user, pwd = acc.get("user"), acc.get("pass")
        session = requests.Session()
        headers = {"User-Agent": "Mozilla/5.0...", "Accept": "text/x-component", "Content-Type": "text/plain;charset=UTF-8"}
        try:
            # 登录
            h_login = headers.copy()
            h_login["Next-Action"] = LOGIN_ACTION_ID
            session.post(f"{BASE_URL}/login", headers=h_login, data=json.dumps([{"username": user, "password": pwd}, "/"]), allow_redirects=False)

            if 'token' not in session.cookies:
                summary.append(f"👤 {user}\n└ ❌ 登录失败")
                continue

            # 签到
            h_checkin = headers.copy()
            h_checkin["Next-Action"] = CHECKIN_ACTION_ID
            r = session.post(f"{BASE_URL}/", headers=h_checkin, data="[{},{}]")
            summary.append(f"👤 {user}\n└ {decode_next_response(r)}")
        except Exception as e:
            summary.append(f"👤 {user}\n└ 💥 异常: {str(e)[:20]}")
        time.sleep(2)

    send_tg_notice(summary)

if __name__ == "__main__":
    run()