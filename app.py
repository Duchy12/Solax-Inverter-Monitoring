from flask import Flask, render_template, redirect
import SolaxTCP
import json
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import datetime
app = Flask(__name__)

# Yes I know bad idea boohoo use ENV variables
token = 'TOKEN'
org = 'YOURORG'
url = 'http://localhost:8086'
bucket = 'Solax'

client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
# ID, TIMESTAMP, VOLTAGE, CURRENT, POWER, TEMP, CHARGE, SOLAR, HOME, GRID

def QueryInflux(timeFrame):
    query = f'from(bucket: "Solax") |> range(start: -{timeFrame})\
    |> filter(fn: (r) => r._measurement == "data")\
    '

    result = client.query_api().query(org=org, query=query)

    results = []
    for table in result:
        for record in table.records:
            results.append((record.get_time(), record.get_field(), record.get_value()))

    # Group the data by timestamp
    data = {}
    for timestamp, field, value in results:
        if timestamp not in data:
            data[timestamp] = {}
        data[timestamp][field] = value

    formatted_data = {dt.strftime('%Y-%m-%d-%H:%M:%S'): value for dt, value in data.items()}
    
    #Only one value from each hour
    formatted_data = {key: value for key, value in formatted_data.items() if key[-5:] == '00:00'}
    return formatted_data


@app.route('/')
def index():
    try:
        voltage, current, power, temp = SolaxTCP.QueryBatteryStats()
    except:
        return redirect('error')
    charge = SolaxTCP.QueryBatteryCharge()
    solar = SolaxTCP.QueryPanelStats()
    home = SolaxTCP.QueryDomacnost()
    grid = SolaxTCP.QueryGridPower()
    liveStats = [voltage, current, power, temp, charge, solar, home, grid]
    graphData = QueryInflux('1d')
    #print(graphData)
    return render_template('index.html', liveStats=liveStats, graphData=graphData)

@app.route('/api')
def api_index():
        return render_template('api.html')


@app.route('/api/battery')
def api_battery():
    try:
        voltage, current, power, temp = SolaxTCP.QueryBatteryStats()
        charge = SolaxTCP.QueryBatteryCharge()
        return json.dumps({'success':True, 'voltage': voltage, 'current': current, 'power': power, 'temp': temp, 'charge': charge }), 200, {'ContentType':'application/json'} 
    except:
        return json.dumps({'success':False}), 200, {'ContentType':'application/json'} 

@app.route('/api/solar')
def api_solar():
    try:
        solar = SolaxTCP.QueryPanelStats()
        return json.dumps({'success':True, 'power': solar }), 200, {'ContentType':'application/json'} 
    except:
        return json.dumps({'success':False}), 200, {'ContentType':'application/json'} 

@app.route('/api/exportgrid')
def api_export():
    try:
        grid = SolaxTCP.QueryGridPower()
        return json.dumps({'success':True, 'export': grid }), 200, {'ContentType':'application/json'} 
    except:
        return json.dumps({'success':False}), 200, {'ContentType':'application/json'} 


@app.route('/api/localgrid')
def api_local():
    try:
        home = SolaxTCP.QueryDomacnost()
        return json.dumps({'success':True, 'export': home }), 200, {'ContentType':'application/json'} 
    except:
        return json.dumps({'success':False}), 200, {'ContentType':'application/json'} 


@app.route('/error')
def error():
    return render_template('error.html')

@app.route('/history')
def history():
    return render_template('history.html', data=QueryInflux('30d'))


if __name__ == '__main__':
    app.run(debug=False, host="192.168.2.40")
