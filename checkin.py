import os
import logging
import requests
import json
import time

# 配置日志格式和级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== 本地配置区 (GitHub 运行时会自动读取 Secrets) ====================
# 1. 账号列表
DEBUG_ACCOUNTS = [
    {"user": "xxx", "pass": "xxx"},
    {"user": "xxx", "pass": "xxx"}
]

# 2. Telegram 配置
TG_TOKEN = "xxx"
TG_CHAT_ID = "xxx" # 记得填入你的数字 ID

# 3. 代理配置（本地测试必开，GitHub 运行会自动忽略）
# PROXIES = {"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"}

# 4. 全局赌狗签到开关配置 (True: 开启, False: 关闭)
GAMBLE_CHECKIN = False
# =====================================================================================

BASE_URL = "https://hdhive.com"
LOGIN_ACTION_ID = "603b753f736d128b24c8b4f894057aa301eda77339"
CHECKIN_ACTION_ID = "40efbc107064215e9eff178b0466274739ba7d9cb4"

# 逻辑：优先读取 GitHub Secrets，如果没有则使用上面的 DEBUG 值
ACCOUNTS_JSON = os.getenv("HD_ACCOUNTS") or json.dumps(DEBUG_ACCOUNTS)
FINAL_TG_TOKEN = os.getenv("TG_TOKEN") or TG_TOKEN
FINAL_TG_CHAT_ID = os.getenv("TG_CHAT_ID") or TG_CHAT_ID
# 逻辑：优先从 Secrets 读取，如果没有则使用代码里的默认值
LOGIN_ACTION_ID = os.getenv("LOGIN_ACTION_ID") or LOGIN_ACTION_ID
CHECKIN_ACTION_ID = os.getenv("CHECKIN_ACTION_ID") or CHECKIN_ACTION_ID

# 全局赌狗签到开关读取（优先读取环境变量）
env_gamble = os.getenv("GAMBLE_CHECKIN")
FINAL_GAMBLE_CHECKIN = env_gamble.lower() == "true" if env_gamble is not None else GAMBLE_CHECKIN


def decode_next_response(response):
    """
    解析服务器返回的 Next.js Server Action 响应，提取成功或错误信息
    """
    try:
        # 强制 UTF-8 解码，解决可能出现的乱码问题
        text = response.content.decode('utf-8')
        logger.debug(f"原始响应内容: {text[:200]}") # 打印前 200 个字符用于调试

        # Server Action 返回的通常是多行文本，每行可能包含一个 JSON 对象
        for line in text.split('\n'):
            if '{"response"' in line or '{"error"' in line:
                # 截取到 JSON 对象的起始位置并解析
                json_str = line[line.find('{'):]
                json_data = json.loads(json_str)
                
                # 提取成功响应信息
                if "response" in json_data:
                    return f"✅ {json_data['response'].get('message', '成功')}"
                
                # 提取错误响应信息
                if "error" in json_data:
                    return f"❌ {json_data['error'].get('description', '失败')}"
    except Exception as e:
        logger.error(f"解析响应数据时发生异常: {e}")
        
    return "❓ 解析异常"

def send_tg_notice(summary):
    """
    发送 Telegram 通知
    """
    if not FINAL_TG_TOKEN or not FINAL_TG_CHAT_ID:
        logger.warning("未配置 Telegram Token 或 Chat ID，跳过发送通知")
        return
        
    logger.info("准备发送 Telegram 通知...")
    # 优化通知的标题和内容格式，增加当前运行模式的标识
    mode_text = "🎲 赌狗签到" if FINAL_GAMBLE_CHECKIN else "🛡️ 普通签到"
    text = f"🚀 <b>HDHive 签到汇总</b> [{mode_text}]\n"
    text += "━━━━━━━━━━━━━━━━━━\n\n"
    text += "\n\n".join(summary)
    text += "\n\n━━━━━━━━━━━━━━━━━━\n"
    text += f"⏰ <i>{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}</i>"

    url = f"https://api.telegram.org/bot{FINAL_TG_TOKEN}/sendMessage"
    
    try:
        response = requests.post(url, json={"chat_id": FINAL_TG_CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True})
        if response.status_code == 200:
            logger.info("Telegram 通知发送成功")
        else:
            logger.error(f"Telegram 通知发送失败，状态码: {response.status_code}, 响应: {response.text}")
    except Exception as e:
        logger.error(f"发送 Telegram 通知时发生异常: {e}")

def run():
    """
    主执行逻辑
    """
    logger.info("========== 开始执行签到任务 ==========")
    logger.info(f"当前签到模式（全局）: {'赌狗签到' if FINAL_GAMBLE_CHECKIN else '普通签到'}")

    try:
        accounts = json.loads(ACCOUNTS_JSON)
        logger.info(f"成功加载了 {len(accounts)} 个账号配置")
    except json.JSONDecodeError:
        logger.error("账号 JSON 格式错误，请检查 HD_ACCOUNTS 环境变量配置")
        return

    summary = []
    
    for index, acc in enumerate(accounts):
        user = acc.get("user")
        pwd = acc.get("pass")

        logger.info(f"--- 处理第 {index + 1} 个账号: {user} ---")

        if not user or not pwd:
            logger.warning(f"账号或密码为空，跳过")
            summary.append(f"👤 未知账号\n└ ❌ 配置不完整")
            continue
            
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", 
            "Accept": "text/x-component", 
            "Content-Type": "text/plain;charset=UTF-8"
        }

        try:
            # 第一步：尝试登录
            logger.info(f"[{user}] 尝试登录...")
            h_login = headers.copy()
            h_login["Next-Action"] = LOGIN_ACTION_ID
            login_payload = [{"username": user, "password": pwd}, "/"]
            
            # 发送登录请求，allow_redirects=False 以捕获 Set-Cookie
            response_login = session.post(
                f"{BASE_URL}/login", 
                headers=h_login, 
                data=json.dumps(login_payload), 
                allow_redirects=False
            )
            
            logger.debug(f"[{user}] 登录响应状态码: {response_login.status_code}")

            # 验证登录是否成功 (检查是否获取到了 token cookie)
            if 'token' not in session.cookies:
                logger.error(f"[{user}] 登录失败: 未能获取到 token cookie")
                summary.append(f"👤 <b>{user}</b>\n  └ ❌ 登录失败")
                continue
                
            logger.info(f"[{user}] 登录成功")

            # 第二步：尝试签到
            logger.info(f"[{user}] 尝试签到...")
            h_checkin = headers.copy()
            h_checkin["Next-Action"] = CHECKIN_ACTION_ID

            # 根据全局赌狗签到开关，构造不同的 payload
            checkin_payload = "[true]" if FINAL_GAMBLE_CHECKIN else "[false]"

            # 发送签到请求
            response_checkin = session.post(
                f"{BASE_URL}/", 
                headers=h_checkin, 
                data=checkin_payload
            )
            
            logger.debug(f"[{user}] 签到响应状态码: {response_checkin.status_code}")
            
            # 解析签到结果
            checkin_result = decode_next_response(response_checkin)
            logger.info(f"[{user}] 签到结果: {checkin_result}")
            summary.append(f"👤 <b>{user}</b>\n  └ {checkin_result}")
            
        except Exception as e:
            logger.exception(f"[{user}] 执行过程中发生异常: {e}")
            summary.append(f"👤 <b>{user}</b>\n  └ 💥 异常: {str(e)[:50]}")
            
        # 账号之间添加短暂延迟，避免请求过于频繁
        time.sleep(2)

    logger.info("所有账号处理完毕，准备发送通知")
    send_tg_notice(summary)
    logger.info("========== 签到任务执行结束 ==========")

if __name__ == "__main__":
    run()