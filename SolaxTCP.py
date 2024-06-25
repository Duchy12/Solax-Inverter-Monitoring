from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder, BinaryPayloadBuilder, Endian
import time
import os

"""
0x0014 - Napeti baterie * 10
0x0015 - Proud baterie * 10
0x0016 - Vykon baterie - W
0x0018 - TEPLOTA BATERIE
0x001C - % BATERIE

0x001A - Elektrickej uplink T/F
0x0046 - feedin_power LSB
0x0047 - feedin_power MSB

0x000A - SolarDC1
0x000B - SolarDC2
0x0002 - VYKON DOMACNOSTI
0x0050 - Daily yield
"""

client = ModbusTcpClient('192.168.2.76')
client.connect()

def flip_int16(i):
    if i > 2**15:
        i = i - 2**16
    return i

def flip_int32(i):
    if i > 2**31:
        i = i - 2**32
    return i

def DecodeSerialNumber(registers):
    decoder = BinaryPayloadDecoder.fromRegisters(registers, byteorder=Endian.BIG)
    res = decoder.decode_string(14).decode('ascii')
    return res

def QuerySerialNumber():
    response = client.read_holding_registers(0, 8, slave=0x01)
    registers = response.registers
    sr = DecodeSerialNumber(registers)
    return sr

def QueryGridPower():
    response = client.read_input_registers(0x0046, 2, slave=0x01)
    registers = response.registers
    value = (registers[1] << 16) | registers[0]
    
    # Check if the number is negative
    value = flip_int32(value)
    
    return value

def QueryBatteryStats():
    response = client.read_input_registers(0x0014, 5, slave=0x01)
    registers = response.registers
    voltage = registers[0] / 10
    current = registers[1]
    current = flip_int16(current) / 10
    power = registers[2]
    power = flip_int16(power)
    temp = registers[4]
    return voltage, current, power, temp

def QueryBatteryCharge():
    response = client.read_input_registers(0x001C, 1, slave=0x01)
    registers = response.registers
    return registers[0]

def QueryPanelStats():
    response = client.read_input_registers(0x000A, 2, slave=0x01)
    registers = response.registers
    power = registers[0] + registers[1]
    return power

def QueryDomacnost():
    response = client.read_input_registers(0x0002, 1, slave=0x001)
    registers = response.registers
    power = registers[0]
    return power

"""# Solax X3 hybrid gen4
while True:
    os.system("clear")
    voltage, current, power, temp = QueryBatteryStats()
    print("==============================================================================")
    print(f"Napeti: {voltage}V, Proud: {current}A, Vykon: {power}W, Teplota: {temp}C, Nabiti baterie: {QueryBatteryCharge()}%")
    print(f"Grid: {QueryGridPower()}W")
    print(f"Solar panel output: {QueryPanelStats()}W")
    print(f"Spotreba domacnosti: {QueryDomacnost()}W")
    print("==============================================================================")
    time.sleep(10)
    """