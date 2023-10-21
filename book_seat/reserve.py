import websocket
import json
import http.client
from .utils import get_seat_key, get_area_id
import schedule
import time


def queue(cookie: str):
    queue_msg = '{"ns":"prereserve/queue","msg":""}'
    url = "wss://wechat.v2.traceint.com/ws?ns=prereserve/queue"
    ws = websocket.WebSocket()
    ws.connect(url, cookie=cookie)
    while True:
        ws.send(queue_msg)
        result = ws.recv()
        result_dict = json.loads(result)
        # print(result_dict)
        if "msg" in result_dict:
            print(result_dict["msg"])
            break
    ws.close()


def reserve_seat(cookie: str, area: str, seat: int):
    if area is None:
        raise RuntimeError("你需要指定区域")
    if seat is None:
        raise RuntimeError("你需要指定座位号")

    # 准备好需要的参数
    seat_key = get_seat_key(area, seat)
    area_id = get_area_id(area)

    stop = False

    def queue_and_reserve(cookie: str):
        # 排队并发送预订请求
        queue(cookie)
        conn = http.client.HTTPSConnection("wechat.v2.traceint.com")
        payload = (
            '{"operationName":"save","query":"mutation save($key: String!, $libid: Int!, $captchaCode: String, $captcha: String) {\\n userAuth {\\n prereserve {\\n save(key: $key, libId: $libid, captcha: $captcha, captchaCode: $captchaCode)\\n }\\n }\\n}","variables":{"key":"'
            + seat_key
            + '.","libid":'
            + str(area_id)
            + ',"captchaCode":"","captcha":""}}'
        )

        headers = {
            "cookie": cookie,
            "Host": "wechat.v2.traceint.com",
            "app-version": "2.0.14",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 NetType/WIFI MicroMessenger/6.8.0(0x16080000) MacWechat/3.8.3(0x13080310) XWEB/30817 Flue",
            "content-type": "application/json",
            "accept": "*/*",
            "origin": "https://web.traceint.com",
            "sec-fetch-site": "same-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://web.traceint.com/",
            "accept-language": "en",
        }

        conn.request("POST", "/index.php/graphql/", payload, headers)

        res = conn.getresponse()
        data = res.read()

        res_text = data.decode("utf-8")
        res_dict = json.loads(res_text)
        # print(res_dict)
        if res_dict["data"]["userAuth"]["prereserve"]["save"]:
            print(f"预约成功：{area} 区 {seat} 号座位")
        else:
            print(res_dict["errors"][0]["msg"])
        nonlocal stop
        stop = True

    # 测试
    # queue_and_reserve(cookie=cookie)
    # return

    # 在 8:10 准时执行
    schedule.every().day.at("20:10").do(queue_and_reserve, cookie=cookie)

    print("正在等待时间到达8:10...")
    while True:
        if stop:
            break
        schedule.run_pending()
        time.sleep(0.01)  # 每 0.01 秒检测一次是否到了预订时间
