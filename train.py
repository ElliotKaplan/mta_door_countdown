from adafruit_datetime import datetime
import gc

import configs
import constants


# specifically for the date header returned by wheresmyfuckingtrain
def process_header_time(datestring):
    index = 0
    index += datestring[index:].find(', ') + 2 # skip the name of the dow
    endind = index + datestring[index:].find(' ')
    day = int(datestring[index:endind])

    index = endind + 1
    endind = index + datestring[index:].find(' ')
    month = constants.CALENDAR[datestring[index:endind]]

    index = endind + 1
    endind = index + datestring[index:].find(' ')
    year = int(datestring[index:endind])

    index = endind + 1
    endind = index + datestring[index:].find(':')
    hour = int(datestring[index:endind])

    index = endind + 1
    endind = index + datestring[index:].find(':')
    minute = int(datestring[index:endind])

    index = endind + 1
    endind = index + datestring[index:].find(' ')
    second = int(datestring[index:endind])

    index = endind + 1
    tz = datestring[index:]
    return datetime(year, month, day, hour, minute, second, )
    
def process_train_buffer(buff, routes, index):
    index += buff[index:].find(b'"route":') + 8
    if index > constants.BUFFSIZE:
        return '', ''
    index += buff[index:].find(b'"') + 1

    if buff[index] in routes:
        route = buff[index]
        index += buff[index:].find(b'"time":') + 8
        index += buff[index:].find(b'"') + 1
        endind = index + buff[index:].find(b'"')
        return route, buff[index:endind].decode()
    return '', ''
        
        

def get_stop_arrivals(request_pool, buff, rowdata, stopid, direction, routes):
    # the response is too big to manage all at once, so we're going to
    # have to handle it as a stream
    # this is going to be jank as fuck
    gc.collect()
    j = 0
    with request_pool.get(constants.SUBWAY_URL + stopid, stream=True) as response:
        index = 0
        # use the header time for the time
        resptime = process_header_time(response.headers['date'])

        # concatenate 2 buffers so that we can find strings across chunks
        iterator = response.iter_content(constants.BUFFSIZE)
        buff[:constants.BUFFSIZE] = next(iterator)
        # find the data in the direction we seek
        for this in iterator:
            buff[constants.BUFFSIZE:] = this
            index = buff.find(direction)
            if (index != -1) and (index < constants.BUFFSIZE):
                index += buff[index:].find(b'[') + 1
                break
            # shift the array
            buff[:constants.BUFFSIZE] = buff[constants.BUFFSIZE:]
            gc.collect()
        # now split off the arrival times. First check the buffer we already have
        thisroute, timestamp = process_train_buffer(buff, routes, index)
        # shift the array
        buff[:constants.BUFFSIZE] = buff[constants.BUFFSIZE:]
        gc.collect()
        for this in iterator:
            index = 0
            buff[constants.BUFFSIZE:] = this
            thisroute, timestamp = process_train_buffer(buff, routes, index)
            if timestamp.startswith('20'): # hey look, a y2k:
                waittime = str(int((datetime.fromisoformat(timestamp).timestamp() - resptime.timestamp()) // 60))
                rowdata[j] = chr(thisroute) + waittime # chr is because of single byte weirdness
                j += 1
            if j >= 3:
                break
                
            # shift the array
            buff[:constants.BUFFSIZE] = buff[constants.BUFFSIZE:]
            gc.collect()
    gc.collect()
