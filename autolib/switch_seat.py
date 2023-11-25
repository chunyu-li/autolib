import http.client
import json
import time
from .occupy_seat import all_area_empty_seats
from .utils import desktop_notify, get_area_id, get_seat_key, init_all_seat_mappings


def get_good_id(cookie: str) -> int:
    conn = http.client.HTTPSConnection("wechat.v2.traceint.com")
    headers = {
        "Cookie": cookie,
        "content-type": "application/json",
    }
    json_data = {
        "operationName": "list",
        "query": "query list($page: Int!, $num: Int!, $isUsed: Int!) {\n userAuth {\n goods {\n list(page: $page, num: $num, isUsed: $isUsed) {\n id\n goods_type\n goods_name\n goods_simple_desc\n is_used\n is_config\n goods_desc\n fail_msg\n succ_msg\n used_time\n img\n num\n }\n }\n }\n}",
        "variables": {
            "page": 1,
            "num": 30,
            "isUsed": 0,
        },
    }
    conn.request("POST", "/index.php/graphql/", json.dumps(json_data), headers)
    response = conn.getresponse()
    data = response.read()

    res_text = data.decode("utf-8")
    res_dict = json.loads(res_text)
    good_id = int(res_dict["data"]["userAuth"]["goods"]["list"][0]["id"])
    return good_id


def switch_seat(cookie: str, good_id: int, area: str, seat: int):
    seat_key = get_seat_key(area, seat)
    area_id = get_area_id(area)

    conn = http.client.HTTPSConnection("wechat.v2.traceint.com")
    headers = {
        "Cookie": cookie,
        "content-type": "application/json",
    }

    json_data = {
        "operationName": "swapseatUseIt",
        "query": "mutation swapseatUseIt($goodId: Int!, $libId: Int!, $seatKey: String!) {\n userAuth {\n goods {\n swapseat {\n useIt(goodId: $goodId, libId: $libId, seatKey: $seatKey)\n }\n }\n }\n}",
        "variables": {
            "goodId": good_id,
            "libId": area_id,
            "seatKey": seat_key,
        },
    }
    conn.request("POST", "/index.php/graphql/", json.dumps(json_data), headers)
    response = conn.getresponse()
    data = response.read()

    res_text = data.decode("utf-8")
    res_dict = json.loads(res_text)
    if res_dict["data"]["userAuth"]["goods"]["swapseat"]["useIt"]:
        desktop_notify("换座", f"换座成功: {area} 区 {seat} 号")
        print(f"换座成功: {area} 区 {seat} 号")
    else:
        desktop_notify("换座", f"换座失败: {area} 区 {seat} 号")
        print("换座失败")


def detect_and_switch(cookie: str, detect_areas: list):
    if detect_areas is None:
        raise RuntimeError("你需要指定检测区域")
    print("切换座位中...")
    init_all_seat_mappings(cookie, detect_areas)
    good_id = get_good_id(cookie)
    while True:
        all_areas_seats = all_area_empty_seats(cookie, detect_areas)
        if all_areas_seats is None:
            break
        if len(all_areas_seats) != 0:
            area, seat = all_areas_seats[0]
            switch_seat(cookie, good_id, area, int(seat))
            break
        time.sleep(1)
