import os
import json
import http.client
import json


def desktop_notify(title: str, info: str):
    os.system(f'osascript -e \'display notification "{info}" with title "{title}"\'')


all_seat_mappings = None


def _init_area_seat_mappings(cookie: str, area_id: int) -> None:
    conn = http.client.HTTPSConnection("wechat.v2.traceint.com")
    headers = {
        "Cookie": cookie,
        "content-type": "application/json",
    }
    json_data = {
        "operationName": "libLayout",
        "query": "query libLayout($libId: Int, $libType: Int) {\n userAuth {\n reserve {\n libs(libType: $libType, libId: $libId) {\n lib_id\n is_open\n lib_floor\n lib_name\n lib_type\n lib_layout {\n seats_total\n seats_booking\n seats_used\n max_x\n max_y\n seats {\n x\n y\n key\n type\n name\n seat_status\n status\n }\n }\n }\n }\n }\n}",
        "variables": {
            "libId": area_id,
        },
    }
    conn.request("POST", "/index.php/graphql/", json.dumps(json_data), headers)
    response = conn.getresponse()

    data = response.read()

    res_text = data.decode("utf-8")
    res_dict = json.loads(res_text)

    area_seat_mappings = {}
    for seat in res_dict["data"]["userAuth"]["reserve"]["libs"][0]["lib_layout"]["seats"]:
        if seat["name"] is None or seat["name"] == "":
            continue
        area_seat_mappings[int(seat["name"])] = seat["key"]
    return area_seat_mappings


def init_all_seat_mappings(cookie: str, detect_areas: list) -> None:
    global all_seat_mappings
    all_seat_mappings = {}
    for area in detect_areas:
        all_seat_mappings[area] = _init_area_seat_mappings(cookie, get_area_id(area))


def get_seat_key(area: str, seat: int) -> dict:
    global all_seat_mappings
    return all_seat_mappings[area][seat]


def get_area_id(area: str) -> int:
    if area == "A":
        return 323
    elif area == "B":
        return 324
    elif area == "mid":
        return 124385
    elif area == "3":
        return 126122
    elif area == "4":
        return 126129
    else:
        raise ValueError("area 输入值错误")
