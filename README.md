# Mta Door Countdown
This is a countdown clock for home use. It is heavily cribbed from [a
friend's verision](https://github.com/CallaJune/mta-dash), with some
modifications for taste. See their repository for better information
as to how to set this up yourself.

I also heavily crib some of the networking
stuff from [the adafruit
libraries](https://github.com/adafruit/Adafruit_CircuitPython_Requests/blob/main/examples/wifi/requests_wifi_simpletest.py),
whence the MIT License.

This is in no way, shape, or form designed for anyone else's
use. There is some jank to how I've managed things like memory
limitations, which results in semiregular reboots of the display. This
is entirely fine for my purposes, but I would not recommend

## What is displayed
The code as written will display arrival times at one bus stop and
three subway stations. These are specified in the `configs.py` file,
which itself reads from the `settings.toml` file where Adafruit
recommends storing wifi connection information. If the right
environmental variables are not set in `settings.toml`, the display
will default to showing arrivals for Court Square, Queensborough
Plaza, and a bus stop in that general vicinity.

### Notes on making requests without an Adafruit API token
MTA-Dash makes use of an Adafruit API to handle the data from
api.wheresthefuckingtrain.com. Basically that offloads the json
parsing to an external source because memory is at a premium on the
MatrixPortal board. Rather than registering with an extra service, MTA
Door Countdown makes requests to api.wheresthefuckingtrain.com and
bustime.mta.info. Since these responses are rather large for the board
to hold all at once, the responses are streamed in chunks. The code
initializes a buffer of 2x the chunk size. As the streams are
processed, new chunks are written into the second half of the buffer,
and then pushed forwards to make room for the new chunks. The idea is
that if some data we want to take note of crosses two chunks, this
short term memory will allow us to mark the data anyways.


#### Parsing bus data
The Bus data comes in the form of an HTML file of about 4kb. Which is
too big for the board to handle at once. To find arrival times we just
look for the 'arrivalAtStop' tag, and scroll forwards until we find
the bolded text. Conveniently bustime.mta.info represents arrivals in
terms of how long you need to wait, which is probably an artifact from
the SMS service.

#### Parsing train data
This comes in the form of a JSON payload. Since I don't know how to
parse a stream on board with the adafruit_requests library, I
jury-rigged a version to pull out route names and arrival timestamps
from the stream as it is churned through. Rather than using the board
time to calculate the arrival time, I use the 'Date' header in the
HTTP response. This is probably suboptimal, but accounts for a failure
to actually get my home network's time onto the board.
