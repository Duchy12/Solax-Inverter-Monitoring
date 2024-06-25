import SolaxTCP
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# Yes I know bad idea boohoo use ENV variables
token = 'TOKEN'
org = 'YOURORG'
url = 'http://localhost:8086'
bucket = 'Solax'

client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

def queryEverything():
    try:
        serial = SolaxTCP.QuerySerialNumber()
    except:
        print('Error: Couldn\'t connect to the inverter')
    voltage, current, power, temp = SolaxTCP.QueryBatteryStats()
    charge = SolaxTCP.QueryBatteryCharge()
    solar = SolaxTCP.QueryPanelStats()
    home = SolaxTCP.QueryDomacnost()
    grid = SolaxTCP.QueryGridPower()
    return serial, voltage, current, power, temp, charge, solar, home, grid

def writeToInfluxDB():
    try:
        serial, voltage, current, power, temp, charge, solar, home, grid = queryEverything()
        point = Point("data").tag("serial", serial).field("voltage", voltage).field("current", current).field("power", power).field("temp", temp).field("charge", charge).field("solar", solar).field("home", home).field("grid", grid)
        write_api.write(bucket=bucket, org=org, record=point)
        print('Data written to InfluxDB')
    except Exception as e:
        print(f'Error writing data to InfluxDB: {str(e)}')

def main():
    while True:
        writeToInfluxDB()
        time.sleep(600)

if __name__ == '__main__':
    main()
