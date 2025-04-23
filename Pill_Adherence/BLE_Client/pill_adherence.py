import boto3
from boto3.dynamodb.conditions import Attr
from decimal import Decimal
import base64
from datetime import datetime

import asyncio
from bleak import BleakClient, BleakScanner
import struct
import numpy as np

# BLE Variables
uuid_pill_status_pill_1_characteristic    = '00000006-8e22-4541-9d4c-21edae82ed19'
EMPTY_THRESHOLD = 10

# Cloud Variables
ACCESS_KEY = ""
SECRET_KEY = ""
REGION = "us-east-2"
table_name = "medication_adherence"  # change this if needed


# Provide a piece of data and place the data into the database.
# Rerun the function with a key set thats already in the database
# will update the data correspond to the key set.
def put_item(dynamodb, table_name, item_data):
    table = dynamodb.Table(table_name)

    try:
        response = table.put_item(Item=item_data)
        # print("PutItem response:", response)
    except Exception as e:
        print("Error inserting data:", e)


# Provide a key set and get data correspond to the key.
def get_item_with_key(dynamodb, table_name, key_data):
    table = dynamodb.Table(table_name)

    try:
        response = table.get_item(Key=key_data)
        print("GetItem response:", response.get("Item"))
    except Exception as e:
        print("Error getting data:", e)


# Provide two attributes (can be keys) and get data correspond to the attributes.
def get_items_with_attr(dynamodb, table_name, key1, value1, key2, value2):
    table = dynamodb.Table(table_name)

    response = table.scan(
        FilterExpression=Attr(key1).eq(value1) & Attr(key2).eq(value2)
    )

    items = response["Items"]
    for item in items:
        print(item)

    # Handle pagination in case of chunking by scan()
    while "LastEvaluatedKey" in response:
        response = table.scan(
            FilterExpression=Attr(key1).eq(value1) & Attr(key2).eq(value2),
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        items.extend(response["Items"])
        for item in response["Items"]:
            print(item)


# Provide a key set and delete data correspond to the key.
def delete_item(dynamodb, table_name, key_data):
    table = dynamodb.Table(table_name)

    try:
        table.delete_item(Key=key_data)
    except Exception as e:
        print("Error deleting data:", e)


def put_item_with_image(dynamodb, table_name, item_data, image_path):
    table = dynamodb.Table(table_name)

    try:
        with open(image_path, "rb") as f:
            image_binary = f.read()

        # 1) using binary for alternative：
        # item_data['image_data'] = image_binary

        # 2) using base64：
        base64_data = base64.b64encode(image_binary).decode("utf-8")
        item_data["image_data"] = base64_data

        response = table.put_item(Item=item_data)
        print("PutItem with image response:", response)
    except Exception as e:
        print("Error inserting data with image:", e)


async def calibrate_organizer(ble_device):
    print("Calibrate Pill Organizer")

    empty_vals = np.zeros(14)

    # Read amd unpack sensor data from substation
    async with BleakClient(ble_device) as client:

        for n in range(100):
            adc_raw = await client.read_gatt_char(uuid_pill_status_pill_1_characteristic)
            h = ''.join(format(byte, ' 02x') for byte in adc_raw)

            adc = struct.unpack('>BBBBBBBBBBBBBB', adc_raw)
            
            for dev in range(14):
                empty_vals[dev] = empty_vals[dev] + adc[dev]

            await asyncio.sleep(.1)

    print("Default empty Values")

    for n in range(14):
        print("Sensor[{}]: {}".format(n, empty_vals[n]))

    return empty_vals

async def main():

    # Connect to BLE device
    print("Initialize BLE communication")
    ble_device = ''
    devices = await BleakScanner.discover(3.0, return_adv=True)
    for d in devices:
        if(devices[d][1].local_name == 'PILL-STM32'):
            ble_device = d
            print("     Found Device ({})".format(ble_device))

            break


    # Create a database instance
    print("Initialize Database Instance")
    session = boto3.Session(
                    aws_access_key_id=ACCESS_KEY, 
                    aws_secret_access_key=SECRET_KEY, 
                    region_name=REGION)
    
    dynamodb = session.resource("dynamodb")


    async with BleakClient(ble_device) as client:

        # Pill Organizer calibration
        print("Calibrate Pill Organizer")
        empty_vals = np.zeros(14)
        meds_found = bool_list = [False] * 14

        N = 20
        for n in range(N):
            adc_raw = await client.read_gatt_char(uuid_pill_status_pill_1_characteristic)
            h = ''.join(format(byte, ' 02x') for byte in adc_raw)

            adc = struct.unpack('>BBBBBBBBBBBBBB', adc_raw)
            
            for dev in range(14):
                empty_vals[dev] = empty_vals[dev] + adc[dev]

            await asyncio.sleep(.5)

        print("Default empty Values")

        for n in range(14):
            empty_vals[n] = int(empty_vals[n]/N)
            print("Sensor[{}]: {}".format(n, empty_vals[n]))

        # Start Main Loop        
        while(1):

            # Read amd unpack sensor data from substation
            adc_raw = await client.read_gatt_char(uuid_pill_status_pill_1_characteristic)
            h = ''.join(format(byte, ' 02x') for byte in adc_raw)

            adc = struct.unpack('>BBBBBBBBBBBBBB', adc_raw)

            for n in range(14):
                if(abs(adc[n] - empty_vals[n]) > EMPTY_THRESHOLD):
                    meds_found[n] = 1
                else:
                    meds_found[n] = 0

            # TODO delete later
            meds_found[0] = 0
            meds_found[1] = 0
            meds_found[2] = 0
            meds_found[3] = 0
            meds_found[4] = 0
            meds_found[5] = 0
            meds_found[6] = 0
            meds_found[7] = 0
            meds_found[9] = 0
            meds_found[11] = 0
            meds_found[13] = 0
            print(meds_found)


            # Format and send to Cloud
            now = datetime.now()

            # Format the datetime object into the desired string format
            formatted_datetime = now.strftime("%Y-%m-%dT%H:%M:%SZ")

            # Place a piece of data in tabel 'medication_adherence'
            item_data = {
                "device_id": "pill_dev_01",  # primary key
                "timestamp": formatted_datetime,  # sorting key
                "sun_am": meds_found[0],
                "sun_pm": meds_found[1],
                "mon_am": meds_found[2],
                "mon_pm": meds_found[3],
                "tue_am": meds_found[4],
                "tue_pm": meds_found[5],
                "wed_am": meds_found[6],
                "wed_pm": meds_found[7],
                "thu_am": meds_found[8],
                "thu_pm": meds_found[9],
                "fri_am": meds_found[10],
                "fri_pm": meds_found[11],
                "sat_am": meds_found[12],
                "sat_pm": meds_found[13],
            }
            put_item(dynamodb, table_name, item_data)\
            
            print("Sent data to Cloud\n")

            await asyncio.sleep(.5)

# Using the special variable 
# __name__
if __name__=="__main__":
    asyncio.run(main())
