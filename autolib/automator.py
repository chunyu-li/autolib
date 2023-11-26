import http.client
import websocket
import schedule
import json
from .utils import desktop_notify
import time


class Automator:
    def __init__(self, cookie: str):
        # 初始化
        self._conn = http.client.HTTPSConnection("wechat.v2.traceint.com")
        self._cookie = cookie
        self._headers = {
            "cookie": cookie,
            "content-type": "application/json",
        }
        self._all_seat_mappings = None

    def _post(self, json_data: dict) -> dict:
        # 发起 post 请求
        self._conn.request("POST", "/index.php/graphql/", json.dumps(json_data), self._headers)
        response = self._conn.getresponse()
        data = response.read()
        res_text = data.decode("utf-8")
        res_dict = json.loads(res_text)
        return res_dict

    def _get_area_seats(self, area: str) -> dict:
        # 获取某区域的所有座位
        area_id = self._get_area_id(area)
        json_data = {
            "operationName": "libLayout",
            "query": "query libLayout($libId: Int, $libType: Int) {\n userAuth {\n reserve {\n libs(libType: $libType, libId: $libId) {\n lib_id\n is_open\n lib_floor\n lib_name\n lib_type\n lib_layout {\n seats_total\n seats_booking\n seats_used\n max_x\n max_y\n seats {\n x\n y\n key\n type\n name\n seat_status\n status\n }\n }\n }\n }\n }\n}",
            "variables": {
                "libId": area_id,
            },
        }
        res_dict = self._post(json_data)
        return res_dict["data"]["userAuth"]["reserve"]["libs"][0]["lib_layout"]["seats"]

    def _area_empty_seats(self, area: str) -> list:
        # 获取某区域的空座位
        seats = self._get_area_seats(area)
        empty_seats = []
        for seat in seats:
            if seat["seat_status"] == 1 and seat["name"] != "":
                empty_seats.append((area, seat["name"]))
        return empty_seats

    def _all_area_empty_seats(self, detect_areas: list) -> list:
        # 获取所有区域的空座位
        all_empty_seats = []
        for area in detect_areas:
            empty_seats = self._area_empty_seats(area)
            all_empty_seats += empty_seats
        return all_empty_seats

    def notify_empty_seats(self, detect_areas: list) -> None:
        # 持续检测空座位并桌面提醒，每隔一秒检测一次
        print("获取空座位中...")
        while True:
            all_empty_seats = self._all_area_empty_seats(detect_areas)
            if len(all_empty_seats) != 0:
                seat_info_list = []
                for area, seat in all_empty_seats:
                    seat_info_list.append(f"{area} 区 {seat} 可用")
                seat_info = ("\n").join(seat_info_list)
                desktop_notify("获取空座位", seat_info)
                print(seat_info)
                break
            time.sleep(1)

    def _occupy_seat(self, area: str, seat: int):
        # 发起占座请求
        seat_key = self._get_seat_key(area, seat)
        area_id = self._get_area_id(area)

        json_data = {
            "operationName": "reserueSeat",
            "query": "mutation reserueSeat($libId: Int!, $seatKey: String!, $captchaCode: String, $captcha: String!) {\n userAuth {\n reserve {\n reserueSeat(\n libId: $libId\n seatKey: $seatKey\n captchaCode: $captchaCode\n captcha: $captcha\n )\n }\n }\n}",
            "variables": {"seatKey": seat_key, "libId": area_id, "captchaCode": "", "captcha": ""},
        }

        res_dict = self._post(json_data)
        if "errors" in res_dict:
            desktop_notify("占座失败", res_dict["errors"][0]["msg"])
            print(res_dict["errors"][0]["msg"])
            print(f"{area} 区 {seat} 号")
            return
        if res_dict["data"]["userAuth"]["reserve"]["reserueSeat"]:
            desktop_notify("占座成功", f"{area} 区 {seat} 号")
            print(f"{area} 区 {seat} 号")

    def detect_and_occupy(self, detect_areas: list):
        # 持续检测空座位并占座，每隔一秒检测一次
        if detect_areas is None:
            raise RuntimeError("你需要指定检测区域")
        print("获取空座位中...")
        self._init_all_seat_mappings(detect_areas)
        while True:
            all_areas_seats = self._all_area_empty_seats(detect_areas)
            if len(all_areas_seats) != 0:
                area, seat = all_areas_seats[0]
                self._occupy_seat(area, int(seat))
                break
            time.sleep(1)

    def _init_area_seat_mappings(self, area: str) -> None:
        # 初始化区域座位映射
        area_id = self._get_area_id(area)
        json_data = {
            "operationName": "libLayout",
            "query": "query libLayout($libId: Int, $libType: Int) {\n userAuth {\n reserve {\n libs(libType: $libType, libId: $libId) {\n lib_id\n is_open\n lib_floor\n lib_name\n lib_type\n lib_layout {\n seats_total\n seats_booking\n seats_used\n max_x\n max_y\n seats {\n x\n y\n key\n type\n name\n seat_status\n status\n }\n }\n }\n }\n }\n}",
            "variables": {
                "libId": area_id,
            },
        }
        res_dict = self._post(json_data)
        area_seat_mappings = {}
        for seat in res_dict["data"]["userAuth"]["reserve"]["libs"][0]["lib_layout"]["seats"]:
            if seat["name"] is None or seat["name"] == "":
                continue
            area_seat_mappings[int(seat["name"])] = seat["key"]
        return area_seat_mappings

    def _init_all_seat_mappings(self, detect_areas: list) -> None:
        # 初始化所有座位的映射
        self._all_seat_mappings = {}
        for area in detect_areas:
            self._all_seat_mappings[area] = self._init_area_seat_mappings(area)

    def _get_seat_key(self, area: str, seat: int) -> dict:
        # 通过映射获取座位 key
        return self._all_seat_mappings[area][seat]

    @staticmethod
    def _get_area_id(area: str) -> int:
        # 获取区域 id
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

    def _get_good_id(self) -> int:
        # 获取换座道具 id
        json_data = {
            "operationName": "list",
            "query": "query list($page: Int!, $num: Int!, $isUsed: Int!) {\n userAuth {\n goods {\n list(page: $page, num: $num, isUsed: $isUsed) {\n id\n goods_type\n goods_name\n goods_simple_desc\n is_used\n is_config\n goods_desc\n fail_msg\n succ_msg\n used_time\n img\n num\n }\n }\n }\n}",
            "variables": {
                "page": 1,
                "num": 30,
                "isUsed": 0,
            },
        }
        res_dict = self._post(json_data)
        goods_list = res_dict["data"]["userAuth"]["goods"]["list"]
        if goods_list == []:
            return None
        else:
            return int(goods_list[0]["id"])

    def _buy_good(self) -> None:
        # 购买换座道具
        json_data = {
            "operationName": "buy",
            "query": "mutation buy($goodsType: String!) {\n userAuth {\n shop {\n buy(goodsType: $goodsType)\n }\n }\n}",
            "variables": {
                "goodsType": "swapseat",
            },
        }
        res_dict = self._post(json_data)
        if res_dict["data"]["userAuth"]["shop"]["buy"]:
            print("购买换座道具成功")
        else:
            raise RuntimeError("购买换座道具失败")

    def _switch_seat(self, good_id: int, area: str, seat: int) -> None:
        # 发起换座请求
        seat_key = self._get_seat_key(area, seat)
        area_id = self._get_area_id(area)

        json_data = {
            "operationName": "swapseatUseIt",
            "query": "mutation swapseatUseIt($goodId: Int!, $libId: Int!, $seatKey: String!) {\n userAuth {\n goods {\n swapseat {\n useIt(goodId: $goodId, libId: $libId, seatKey: $seatKey)\n }\n }\n }\n}",
            "variables": {
                "goodId": good_id,
                "libId": area_id,
                "seatKey": seat_key,
            },
        }
        res_dict = self._post(json_data)

        if res_dict["data"]["userAuth"]["goods"]["swapseat"]["useIt"]:
            desktop_notify("换座成功", f"{area} 区 {seat} 号")
            print(f"{area} 区 {seat} 号")
        else:
            desktop_notify("换座失败", f"{area} 区 {seat} 号")
            print(f"{area} 区 {seat} 号")

    def detect_and_switch(self, detect_areas: list):
        # 持续检测空座位并换座，每隔一秒检测一次
        if detect_areas is None:
            raise RuntimeError("你需要指定检测区域")
        print("切换座位中...")
        self._init_all_seat_mappings(detect_areas)
        good_id = self._get_good_id()
        if good_id is None:
            self._buy_good()
            good_id = self._get_good_id()
        while True:
            all_areas_seats = self._all_area_empty_seats(detect_areas)
            if all_areas_seats is None:
                break
            if len(all_areas_seats) != 0:
                area, seat = all_areas_seats[0]
                self._switch_seat(good_id, area, int(seat))
                break
            time.sleep(1)

    def _queue(self) -> None:
        # 排队
        queue_msg = '{"ns":"prereserve/queue","msg":""}'
        url = "wss://wechat.v2.traceint.com/ws?ns=prereserve/queue"
        ws = websocket.WebSocket()
        ws.connect(url, cookie=self._cookie)
        while True:
            ws.send(queue_msg)
            result = ws.recv()
            result_dict = json.loads(result)
            if "msg" in result_dict:
                print(result_dict["msg"])
                break
        ws.close()

    def reserve_seat(self, area: str, seat: int) -> None:
        # 预约座位
        if area is None:
            raise RuntimeError("你需要指定区域")
        if seat is None:
            raise RuntimeError("你需要指定座位号")

        # 准备好需要的参数
        seat_key = self._get_seat_key(area, seat)
        area_id = self._get_area_id(area)

        stop = False

        def queue_and_reserve():
            # 排队并发送预订请求
            self._queue()

            json_data = {
                "operationName": "save",
                "query": "mutation save($key: String!, $libid: Int!, $captchaCode: String, $captcha: String) {\n userAuth {\n prereserve {\n save(key: $key, libId: $libid, captcha: $captcha, captchaCode: $captchaCode)\n }\n }\n}",
                "variables": {"key": seat_key + ".", "libid": area_id, "captchaCode": "", "captcha": ""},
            }
            res_dict = self._post(json_data)

            if res_dict["data"]["userAuth"]["prereserve"]["save"]:
                print(f"预约成功：{area} 区 {seat} 号座位")
            else:
                print(res_dict["errors"][0]["msg"])
            nonlocal stop
            stop = True

        # 测试
        # queue_and_reserve()
        # return

        # 在 8:10 准时执行
        schedule.every().day.at("20:10").do(queue_and_reserve)

        print("正在等待时间到达8:10...")
        self._init_all_seat_mappings([area])
        while True:
            if stop:
                break
            schedule.run_pending()
            time.sleep(0.01)  # 每 0.01 秒检测一次是否到了预订时间
