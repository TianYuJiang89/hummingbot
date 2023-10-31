import os
from datetime import datetime

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

url = "http://localhost:8086"
org = "hummingbot"
bucket = "new"

token = os.getenv("INFLUXDB_TOKEN")

# client = InfluxDBClient(url=url, username="hummingbot", password="verysecret")
client = InfluxDBClient(url=url, token=token)
write_api = client.write_api(write_options=SYNCHRONOUS)

if __name__ == '__main__':
    exchange = "gate_io_paper_trade"
    ticker = "BTC-USDT"
    price = 4000
    bucket = "new"

    print("token=", token)

    quote_list = []
    quote = Point("quotes")
    quote.tag("exchange", exchange)
    quote.tag("ticker", ticker)
    quote.field("price", price)
    quote.time(datetime.utcnow(), WritePrecision.NS)
    quote_list.append(quote)

    quote = Point("quotes")
    quote.tag("exchange", exchange)
    quote.tag("ticker", ticker + "2")
    quote.field("price", price)
    quote.time(datetime.utcnow(), WritePrecision.NS)
    quote_list.append(quote)

    write_api.write(bucket=bucket, record=quote_list, org=org)
