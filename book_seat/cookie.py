import urllib.request
import urllib.parse
import http.cookiejar
import http.cookies
import requests
import json
import os
from .utils import display_desktop_notification


def check_cookie(cookie: str) -> None:
    if is_cookie_expired(cookie):
        display_desktop_notification("cookie 检验", "cookie 已过期，请重新获取")
        raise ValueError("cookie 已过期，请重新获取")


def write_cookie(cookie: str):
    json_filepath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "json-files", "cookie.json"
    )
    with open(json_filepath, "w") as f:
        json.dump({"cookie": cookie}, f)


def read_cookie() -> str:
    json_filepath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "json-files", "cookie.json"
    )
    with open(json_filepath) as f:
        data = json.load(f)
        return data["cookie"]


def get_code(url):
    query = urllib.parse.urlparse(url).query
    codes = urllib.parse.parse_qs(query).get("code")
    if codes:
        return codes.pop()
    else:
        raise ValueError("Code not found in URL")


def get_cookie_string(code):
    cookiejar = http.cookiejar.MozillaCookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar))
    opener.open(
        "http://wechat.v2.traceint.com/index.php/urlNew/auth.html?"
        + urllib.parse.urlencode(
            {"r": "https://web.traceint.com/web/index.html", "code": code, "state": 1}
        )
    )
    cookie_items = []
    for cookie in cookiejar:
        cookie_items.append(f"{cookie.name}={cookie.value}")
    cookie_string = "; ".join(cookie_items)
    return cookie_string


def get_cookie_from_url(url: str):
    cache_cookie = read_cookie()
    if not is_cookie_expired(cache_cookie):
        return cache_cookie
    code = get_code(url)
    cookie_string = get_cookie_string(code)
    write_cookie(cookie_string)
    return cookie_string


def is_cookie_expired(cookie_string: str) -> bool:
    session = requests.Session()
    cookie = http.cookies.SimpleCookie()
    cookie.load(cookie_string)
    for key, morsel in cookie.items():
        session.cookies.set(key, morsel)

    if session.cookies.keys().count("Authorization") > 1:
        session.cookies.set("Authorization", domain="", value=None)
    res = session.post(
        "http://wechat.v2.traceint.com/index.php/graphql/",
        json={
            "query": 'query getUserCancleConfig { userAuth { user { holdValidate: getSchConfig(fields: "hold_validate", extra: true) } } }',
            "variables": {},
            "operationName": "getUserCancleConfig",
        },
    )
    try:
        result = res.json()
    except json.decoder.JSONDecodeError as err:
        print("Error: %s" % err)
    if result.get("errors") and result.get("errors")[0].get("code") != 0:
        return True
    return False
