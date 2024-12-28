# Personal Configs
from os import getenv

# use the settings.toml file so that I don't have to dox myself here
# default to Court Square stops
stopcode = getenv('STOPCODE', '551923')
bus_no = getenv('BUS_NO', '67')

# direction has the weird encoding to account for how the json from
# wheresmyfuckingtrain is parsed
station_1 = getenv('STATION_1', '718')
lines_1 = getenv('LINES_1', 'W7').encode()
direction_1 = b'"' + getenv('DIRECTION_1', 'S').encode() + b'"'

station_2 = getenv('STATION_2', '719')
lines_2 = getenv('LINES_2', 'E ').encode()
direction_2 = b'"' + getenv('DIRECTION_1', 'S').encode() + b'"'

station_3 = getenv('STATION_3', '719')
lines_3 = getenv('LINES_3', 'G ').encode()
direction_3 = b'"' + getenv('DIRECTION_1', 'S').encode() + b'"'

# Hardware configs
UPDATE_DELAY = 3  # in seconds
SYNC_TIME_DELAY = 60 # in seconds; syncs to network time every so often to prevent drift
RESET_DELAY = 7200 # CircuitPython runs out of sockets occasionally. Reset it periodically.
ERROR_RESET_THRESHOLD = 30 # number of caught errors before the board restarts
