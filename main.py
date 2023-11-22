import argparse
from argparse import RawTextHelpFormatter
from autolib import (
    detect_and_occupy,
    detect_and_switch,
    notify_empty_seats,
    reserve_seat,
    get_cookie_from_url,
    check_cookie,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="BJTU 我去图书馆自动占座脚本",
        add_help=False,
        formatter_class=RawTextHelpFormatter,
    )
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="显示帮助信息",
    )
    parser.add_argument(
        "--task",
        type=str,
        required=True,
        choices=["occupy-seat", "switch-seat", "notify-empty-seats", "reserve"],
        help="你可以选择以下任务:\n"
        + "occupy-seat: 持续检测是否有空座位，有就自动选座\n"
        + "switch-seat: 持续检测是否有空座位，并用使用换座道具\n"
        + "notify-empty-seats: 持续检测是否有空座位，有就桌面提醒\n"
        + "reserve: 预约明天的座位，程序会在 8:10 定时预约",
    )
    parser.add_argument(
        "--cookie",
        type=str,
        default=None,
        help="用来访问的cookie，你需要通过抓包来获取",
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="cookie的替代品，通过微信扫码并复制链接获得",
    )
    parser.add_argument(
        "--reserve-area",
        type=str,
        dest="reserve_area",
        choices=["A", "B", "mid", "3", "4"],
        help="预约区域，A代表5层A区，B代表5层B区，mid代表5层中厅，3代表第三自习室，4代表第四自习室",
    )
    parser.add_argument(
        "--reserve-seat",
        type=int,
        dest="reserve_seat",
        help="预约座位号",
    )
    parser.add_argument(
        "--detect-areas",
        type=str,
        nargs="+",
        dest="detect_areas",
        help="检测哪个区域的座位，你可以输入多个区域，输入区域的顺序将决定优先选的座位",
    )

    return parser.parse_args()


def main(args):
    if not args.cookie and args.url:
        args.cookie = get_cookie_from_url(args.url)
    check_cookie(args.cookie)
    if args.task == "occupy-seat":
        detect_and_occupy(args.cookie, detect_areas=args.detect_areas)
    elif args.task == "switch-seat":
        detect_and_switch(args.cookie, detect_areas=args.detect_areas)
    elif args.task == "reserve":
        reserve_seat(args.cookie, args.reserve_area, args.reserve_seat)
    elif args.task == "notify-empty-seats":
        notify_empty_seats(cookie=args.cookie, detect_areas=args.detect_areas)
    else:
        raise ValueError("task 输入值错误")


if __name__ == "__main__":
    args = parse_args()
    main(args)
