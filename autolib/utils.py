import os
import json


def desktop_notify(title: str, info: str):
    os.system(f'osascript -e \'display notification "{info}" with title "{title}"\'')


def get_seat_key(area: str, seat: int) -> str:
    if area == "A":
        filename = "study-room-a.json"
    elif area == "B":
        filename = "study-room-b.json"
    elif area == "mid":
        filename = "study-room-mid.json"
    elif area == "3":
        filename = "study-room-3.json"
    elif area == "4":
        filename = "study-room-4.json"
    else:
        raise ValueError("area 输入值错误")

    json_filepath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "json-files", filename
    )
    with open(json_filepath) as json_file:
        data = json.load(json_file)
        return data[str(seat)]


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
