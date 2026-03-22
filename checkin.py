import requests
import json
import time

# ==================== 本地测试配置区 ====================
# 1. 账号列表（支持无限添加）
DEBUG_ACCOUNTS = [
    {"user": "xxx", "pass": "xxx"},
    {"user": "xxx", "pass": "xxx"},
]

# 2. Telegram 配置
TG_TOKEN = "xxx"
TG_CHAT_ID = "xxx" # 记得填入你通过 userinfobot 获取的数字 ID

# 3. 代理配置（本地测试必开，部署到 GitHub 时脚本会自动忽略或设为 None）
PROXIES = {
    "http": "http://127.0.0.1:7897",
    "https": "http://127.0.0.1:7897"
}

# 4. 接口关键 ID
BASE_URL = "https://hdhive.com"
LOGIN_ACTION_ID = "601d84138632d39f16adfce544ceb527a6f6243670"
CHECKIN_ACTION_ID = "409539c7faa0ad25d3e3e8c21465c10661896ca5a2"
# ======================================================

def decode_next_response(response):
    """处理 Next.js 响应流并修复 UTF-8 乱码"""
    try:
        # 强制使用 utf-8 解码内容
        content = response.content.decode('utf-8')
        for line in content.split('\n'):
            if '{"error"' in line or '"success"' in line:
                start_idx = line.find('{')
                data = json.loads(line[start_idx:])
                if "error" in data:
                    err = data['error']
                    return f"❌ {err.get('description', '未知原因')}"
                return "✅ 签到成功"
    except Exception as e:
        return f"⚠️ 解析异常: {str(e)[:20]}"
    return "❓ 未知响应格式"

def send_tg_summary(results):
    """发送汇总通知"""
    if not TG_TOKEN or "你的" in TG_TOKEN:
        print("[!] 未配置 TG 信息，仅控制台输出结果。")
        return

    report = "🚀 <b>HDHive 多账号签到汇总</b>\n"
    report += f"📅 时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += "--------------------------------\n"
    report += "\n".join(results)

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": report,
        "parse_mode": "HTML"
    }
    try:
        res = requests.post(url, json=payload, timeout=15, proxies=PROXIES)
        if res.status_code == 200:
            print("[+] Telegram 汇总通知发送成功！")
        else:
            print(f"[!] TG 发送失败: {res.text}")
    except Exception as e:
        print(f"[!] TG 连接异常: {e}")

def main():
    print(f"=== 任务启动: 共 {len(DEBUG_ACCOUNTS)} 个账号 ===")
    summary_list = []

    for i, acc in enumerate(DEBUG_ACCOUNTS):
        user = acc.get("user")
        pwd = acc.get("pass")
        print(f"\n[*] [{i+1}/{len(DEBUG_ACCOUNTS)}] 正在处理: {user}")

        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
            "Accept": "text/x-component",
            "Content-Type": "text/plain;charset=UTF-8",
        }

        try:
            # 1. 登录
            login_headers = headers.copy()
            login_headers["Next-Action"] = LOGIN_ACTION_ID
            login_payload = [{"username": user, "password": pwd}, "/"]

            session.post(f"{BASE_URL}/login", headers=login_headers,
                         data=json.dumps(login_payload), allow_redirects=False)

            if 'token' not in session.cookies:
                msg = "❌ 登录失败 (Cookie 未生成)"
                print(f"    {msg}")
                summary_list.append(f"👤 {user}\n└ {msg}")
                continue

            # 2. 签到
            checkin_headers = headers.copy()
            checkin_headers["Next-Action"] = CHECKIN_ACTION_ID
            r_checkin = session.post(f"{BASE_URL}/", headers=checkin_headers, data="[{},{}]")

            # 3. 解析
            status_text = decode_next_response(r_checkin)
            print(f"    结果: {status_text}")
            summary_list.append(f"👤 {user}\n└ {status_text}")

        except Exception as e:
            error_info = f"💥 运行异常: {str(e)[:30]}"
            print(f"    {error_info}")
            summary_list.append(f"👤 {user}\n└ {error_info}")

        # 账号间隔，防止触发风控
        if i < len(DEBUG_ACCOUNTS) - 1:
            time.sleep(3)

    # 4. 发送汇总
    send_tg_summary(summary_list)
    print("\n=== 所有任务处理完毕 ===")

if __name__ == "__main__":
    main()