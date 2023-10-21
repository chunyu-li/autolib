import http.client
import json
import time
from .utils import display_desktop_notification, get_area_id, get_seat_key


def request_area(cookie: str, area: str) -> list:
    """
    获取图书馆某区所有座位信息

    Args:
        cookie (str): cookie 每一段时间需要更新一次
        area (str, optional): A区 or B区

    Returns:
        list: 座位信息
    """

    conn = http.client.HTTPSConnection("wechat.v2.traceint.com")

    area_id = get_area_id(area)

    payload = (
        '{"operationName":"libLayout","query":"query libLayout($libId: Int, $libType: Int) {\\n userAuth {\\n reserve {\\n libs(libType: $libType, libId: $libId) {\\n lib_id\\n is_open\\n lib_floor\\n lib_name\\n lib_type\\n lib_layout {\\n seats_total\\n seats_booking\\n seats_used\\n max_x\\n max_y\\n seats {\\n x\\n y\\n key\\n type\\n name\\n seat_status\\n status\\n }\\n }\\n }\\n }\\n }\\n}","variables":{"libId":'
        + str(area_id)
        + "}}"
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
    if "errors" in res_dict:
        display_desktop_notification("错误信息", res_dict["errors"])
        print("错误信息", res_dict["errors"])
        return None
    return res_dict["data"]["userAuth"]["reserve"]["libs"][0]["lib_layout"]["seats"]


def area_empty_seats(cookie: str, area: str) -> list:
    seats_list = request_area(cookie, area)
    if seats_list is None:
        return None
    empty_seats_list = []
    for seat in seats_list:
        if seat["seat_status"] == 1 and seat["name"] != "":
            empty_seats_list.append((area, seat["name"]))
    return empty_seats_list


def all_area_empty_seats(cookie: str, detect_areas: list) -> list:
    all_areas_seats = []
    for area in detect_areas:
        seats_list = area_empty_seats(cookie, area)
        if seats_list is None:
            return None
        all_areas_seats += seats_list
    return all_areas_seats


def notify_empty_seats(cookie: str, detect_areas: list):
    print("获取空座位中...")
    start_time = time.monotonic()
    while True:
        all_areas_seats = all_area_empty_seats(cookie, detect_areas)
        if all_areas_seats is None:
            break
        if len(all_areas_seats) != 0:
            seat_info_list = []
            for area, seat in all_areas_seats:
                seat_info_list.append(f"{area} 区 {seat} 可用")
            seat_info = ("\n").join(seat_info_list)
            display_desktop_notification("获取空座位", seat_info)
            print(seat_info)
            break
        time.sleep(1 - ((time.monotonic() - start_time) % 1))  # 每秒检测一次空座位


def book_seat(cookie: str, area: str, seat: int):
    seat_key = get_seat_key(area, seat)
    area_id = get_area_id(area)

    conn = http.client.HTTPSConnection("wechat.v2.traceint.com")

    payload = (
        '{"operationName":"reserueSeat","query":"mutation reserueSeat($libId: Int!, $seatKey: String!, $captchaCode: String, $captcha: String!) {\\n userAuth {\\n reserve {\\n reserueSeat(\\n libId: $libId\\n seatKey: $seatKey\\n captchaCode: $captchaCode\\n captcha: $captcha\\n )\\n }\\n }\\n}","variables":{"seatKey":"'
        + seat_key
        + '","libId":'
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
    if "errors" in res_dict:
        display_desktop_notification("选座", res_dict["errors"][0]["msg"])
        print(res_dict["errors"][0]["msg"])
        return
    if res_dict["data"]["userAuth"]["reserve"]["reserueSeat"]:
        display_desktop_notification("选座", f"选座成功: {area} 区 {seat}")
        print(f"选座成功: {area} 区 {seat}")


def book_empty_seat(cookie: str, detect_areas: list):
    if detect_areas is None:
        raise RuntimeError("你需要指定检测区域")
    print("获取空座位中...")
    start_time = time.monotonic()
    while True:
        all_areas_seats = all_area_empty_seats(cookie, detect_areas)
        if all_areas_seats is None:
            break
        if len(all_areas_seats) != 0:
            area, seat = all_areas_seats[0]
            book_seat(cookie, area, int(seat))
            break
        time.sleep(1 - ((time.monotonic() - start_time) % 1))  # 每秒检测一次空座位
