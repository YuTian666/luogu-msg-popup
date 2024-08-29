import json
import time
import websocket
from win11toast import toast
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format=''
)

# 常量
WS_ENDPOINT = "wss://ws.luogu.com.cn/ws"
COOKIE_PATH = "settings.txt"
MAX_ATTEMPTS = 5
RETRY_INTERVAL = 5


def load_cookies(cookie_path):
    """从文件加载Cookies"""
    try:
        with open(COOKIE_PATH, 'r', encoding='utf-8') as f:
            line = f.readline().strip()  # 读取文件中的第一行并去掉换行符
            user_id, client_id = line.split()
        return user_id, client_id
    except FileNotFoundError:
        logging.error("未找到setting.json")
        return None, None


def generate_headers(user_id, client_id):
    """生成WebSocket连接所需的头信息"""
    return {"Cookie": f"_uid={user_id}; __client_id={client_id}"}


def handle_open(ws):
    """处理WebSocket连接打开事件"""
    logging.info("启动！")
    payload = json.dumps({
        "channel": "chat",
        "channel_param": ws.user_id,
        "type": "join_channel"
    })
    ws.send(payload)


def handle_close(ws, close_status_code, close_msg):
    """处理WebSocket连接关闭事件"""
    logging.warning("连接已关闭")


def handle_message(ws, message):
    """处理收到的WebSocket消息"""
    data = json.loads(message)
    if data.get("_ws_type") == "server_broadcast":
        msg = data["message"]
        logging.info(
            f'收到一条私信来自{msg["sender"]["uid"]}'
        )
        if str(msg["sender"]["uid"]) != str(ws.user_id):
            button_open = {
                "activationType": "protocol",
                "arguments": f'https://www.luogu.com.cn/chat?uid={msg["sender"]["uid"]}',
                "content": "查看私信"
            }
            toast(
                f"{msg["sender"]["name"]}:",
                f'{msg["content"]}',
                duration="short",
                buttons=[button_open, "取消"],
                audio={"silent": "true"}
            )


def establish_connection(headers, user_id):
    """创建WebSocket连接并管理重连"""
    reconnect_count = 0
    while reconnect_count < MAX_ATTEMPTS:
        ws = websocket.WebSocketApp(
            WS_ENDPOINT,
            on_open=handle_open,
            on_message=handle_message,
            on_close=handle_close,
            header=headers
        )
        ws.user_id = user_id  # 在WebSocketApp实例中存储用户ID

        ws.run_forever()
        reconnect_count += 1
        logging.info(
            f'重新连接中 ({reconnect_count}/{MAX_ATTEMPTS})'
        )
        time.sleep(RETRY_INTERVAL)

    logging.error("发生错误，退出程序")
    toast("Timeout")


def main():
    """主函数，启动WebSocket连接"""
    user_id, client_id = load_cookies(COOKIE_PATH)
    if not user_id or not client_id:
        logging.error("Cookie失效")
        return

    headers = generate_headers(user_id, client_id)
    establish_connection(headers, user_id)


if __name__ == "__main__":
    main()
