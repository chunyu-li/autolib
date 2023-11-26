# BJTU 图书馆自动占座脚本

## 安装依赖

```shell
pip install -r requirements.txt
```

### 查看帮助信息

```python
python main.py -h
```

## 使用案例

自动检测第三自习室的空座位并占座

```shell
python main.py \
    --task occupy-seat \
    --detect-areas 3 \
    --url "http://wechat.v2.traceint.com/index.php/graphql/?operationName=index&query=query%7BuserAuth%7BtongJi%7Brank%7D%7D%7D&code=001I9pFa16U9jG0SnkFa1wi4jX3I9pF2&state=1"
```

## 微信扫码获取链接步骤

1. 使用微信扫描下方二维码：

   <img src="./docs/qr.png" alt="qr" width="200px" />

2. 点击微信右上角“…”符号，选择“复制链接”。

   <img src="./docs/copy-url.png" alt="copy-url" width="200px" />