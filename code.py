from os import getenv
import time

import board
import busio
import adafruit_connection_manager
import microcontroller
from board import NEOPIXEL
from digitalio import DigitalInOut
import displayio
import gc
from adafruit_display_text import label
from adafruit_datetime import datetime
from adafruit_bitmap_font import bitmap_font
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network
from adafruit_display_shapes import line
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_requests

import train
import bus
import constants
import configs


print('initializing')

# --- Display setup ---
matrix = Matrix(rotation=180)
display = matrix.display

# --- Drawing setup ---
group = displayio.Group()
primary_font = bitmap_font.load_font("fonts/6x10.bdf")
thumbnail_font = bitmap_font.load_font("fonts/tom-thumb.bdf")


columns = [0, 16, 32, 48]
rows = [11, 19, 26]

# Very personalized display, I only care about inbound
header = [
    label.Label(primary_font, color=constants.ROUTE_COLORS["BUS"], x=columns[0], y=3, text=configs.bus_no),
    label.Label(primary_font, color=constants.ROUTE_COLORS[configs.lines_1[0]], x=columns[1], y=3, text=chr(configs.lines_1[0])),
    label.Label(primary_font, color=constants.ROUTE_COLORS[configs.lines_1[1]], x=columns[1]+5, y=3, text=chr(configs.lines_1[1])),
    label.Label(primary_font, color=constants.ROUTE_COLORS[configs.lines_2[0]], x=columns[2], y=3, text=chr(configs.lines_2[0])),
    label.Label(primary_font, color=constants.ROUTE_COLORS[configs.lines_2[1]], x=columns[2]+5, y=3, text=chr(configs.lines_2[1])),
    label.Label(primary_font, color=constants.ROUTE_COLORS[configs.lines_3[0]], x=columns[3], y=3, text=chr(configs.lines_3[0])),
    label.Label(primary_font, color=constants.ROUTE_COLORS[configs.lines_3[1]], x=columns[3]+5, y=3, text=chr(configs.lines_3[1])),
]
for lab in header:
    group.append(lab)

# underscore so we can see which column updated last
underscores = [line.Line(c, 31, c+11, 31, 0xA00000) for c in columns]
for underscore in underscores:
    group.append(underscore)
    
# initialize the diplay blocks
blocks = list()
for col in columns:
    blocks.append(list())
    for row in rows:
        blocks[-1].append(
            label.Label(primary_font, color=constants.ROUTE_COLORS["BUS"], x=col, y=row, text='--')
        )
        group.append(blocks[-1][-1])
display.root_group = group


### Cribbed from https://github.com/adafruit/Adafruit_CircuitPython_Requests/blob/main/examples/wifi/requests_wifi_simpletest.py ###
# --- Network Setup --- 
# Set up the wifi access and the requests pool
secrets = {
    "ssid": getenv("CIRCUITPY_WIFI_SSID"),
    "password": getenv("CIRCUITPY_WIFI_PASSWORD"),
}

# If you are using a board with pre-defined ESP32 Pins:
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

# Secondary (SCK1) SPI used to connect to WiFi board on Arduino Nano Connect RP2040
if "SCK1" in dir(board):
    spi = busio.SPI(board.SCK1, board.MOSI1, board.MISO1)
else:
    spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

pool = adafruit_connection_manager.get_radio_socketpool(esp)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(esp)
request_pool = adafruit_requests.Session(pool, ssl_context)

print("Connecting to AP...")
while not esp.is_connected:
    try:
        esp.connect_AP(secrets["ssid"], secrets["password"])
    except OSError as e:
        print("could not connect to AP, retrying: ", e)
        continue
print("Connected to", esp.ap_info.ssid, "\tRSSI:", esp.ap_info.rssi)
print("My IP address is", esp.ipv4_address)
### END of Cribbed Code ###


# initialize a buffer to try to limit the number of memory allocation errors
buff = bytearray(2*constants.BUFFSIZE)

print('initialization over')
for under in underscores:
    under.color = 0x000000

# # --- Main loop ---
# last_reset = time.monotonic()
# last_time_sync = None
# it_dir = 0
# error_counter = 0

# allocate memory for processing request streams
rowdata = ['', '', '']
while True:
    try:
        # empty the rowdata
        for i, _ in enumerate(rowdata):
            rowdata[i] = '--'
        bus.get_stop_arrivals(request_pool, buff, rowdata, configs.stopcode)
        for arrival, row in zip(rowdata, blocks[0]):
            row.text = arrival
        underscores[0].color = 0xA00000
        underscores[3].color = 0x000000

        # empty the rowdata
        for i, _ in enumerate(rowdata):
            rowdata[i] = 'X--'
        train.get_stop_arrivals(request_pool, buff, rowdata, configs.station_1, configs.direction_1, configs.lines_1)
        for arrival, row in zip(rowdata, blocks[1]):
            row.text = arrival[1:]
            row.color = constants.ROUTE_COLORS[ord(arrival[0])]
        underscores[1].color = 0xA00000
        underscores[0].color = 0x000000

        # empty the rowdata
        for i, _ in enumerate(rowdata):
            rowdata[i] = 'X--'
        train.get_stop_arrivals(request_pool, buff, rowdata, configs.station_2, configs.direction_2, configs.lines_2)
        for arrival, row in zip(rowdata, blocks[2]):
            row.text = arrival[1:]
            row.color = constants.ROUTE_COLORS[ord(arrival[0])]
        underscores[2].color = 0xA00000
        underscores[1].color = 0x000000

        # empty the rowdata
        for i, _ in enumerate(rowdata):
            rowdata[i] = 'X--'
        train.get_stop_arrivals(request_pool, buff, rowdata, configs.station_3, configs.direction_3, configs.lines_3)
        for arrival, row in zip(rowdata, blocks[3]):
            row.text = arrival[1:]
            row.color = constants.ROUTE_COLORS[ord(arrival[0])]
        underscores[3].color = 0xA00000
        underscores[2].color = 0x000000

    except Exception as e:
        print(e)
        print('restarting')
        microcontroller.reset()
