from flask import Flask, request
from threading import Thread, Event
import time
import boto3
from decimal import Decimal
from datetime import datetime

ACCESS_KEY = "AKIA2ZIONITL6DXD7Y6O"
SECRET_KEY = "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"
REGION     = "us-east-2"
TABLE_NAME = "PMCO2_sensors"

session = boto3.Session(
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name=REGION
)
dynamodb = session.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

app = Flask(__name__)

latest_mq = {}
latest_pm = {}

@app.route("/sensor", methods=["GET"])
def sensor_data():
    if "rzero" in request.args:
        latest_mq.update({
            "rzero": Decimal(request.args["rzero"]),
            "corrected_rzero": Decimal(request.args["corrected_rzero"]),
            "resistance": Decimal(request.args["resistance"]),
            "ppm": Decimal(request.args["ppm"]),
            "corrected_ppm": Decimal(request.args["corrected_ppm"]),
        })
        print("Updated latest MQ‑135:", latest_mq)

    # detect PM2.5 fields
    if "pm10_std" in request.args:
        latest_pm.update({
            "pm10_std": Decimal(request.args["pm10_std"]),
            "pm25_std": Decimal(request.args["pm25_std"]),
            "pm100_std": Decimal(request.args["pm100_std"]),
            "pm10_env": Decimal(request.args["pm10_env"]),
            "pm25_env": Decimal(request.args["pm25_env"]),
            "pm100_env": Decimal(request.args["pm100_env"]),
            "p03": Decimal(request.args["p03"]),
            "p05": Decimal(request.args["p05"]),
            "p10": Decimal(request.args["p10"]),
            "p25": Decimal(request.args["p25"]),
            "p50": Decimal(request.args["p50"]),
            "p100": Decimal(request.args["p100"]),
        })
        print("Updated latest PM2.5:", latest_pm)

    return "OK", 200

def uploader_loop(interval_s: float, stop_evt: Event):
    """
    Every `interval_s` seconds, push a combined record
    (if we have both MQ and PM data) into DynamoDB.
    """
    while not stop_evt.is_set():
        time.sleep(interval_s)

        if latest_mq and latest_pm:
            item = {
                "device_id": "raspi-pico-2w",  # match your table's key schema
                "timestamp": datetime.utcnow().isoformat() + "Z",
                **latest_mq,
                **latest_pm
            }
            try:
                table.put_item(Item=item)
                print("Uploaded to DynamoDB:", item)
            except Exception as e:
                print("DynamoDB upload error:", e)
        else:
            print("Waiting for both MQ‑135 & PM2.5 data...")

if __name__ == "__main__":
    stop_event = Event()
    uploader = Thread(target=uploader_loop, args=(10.0, stop_event), daemon=True)
    uploader.start()

    app.run(host="0.0.0.0", port=5000)

    stop_event.set()
