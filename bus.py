import gc
import time

import constants

def get_stop_arrivals(request_pool, buff, rowdata, stopid):
    gc.collect()
    j = 0
    with request_pool.get(constants.BUS_URL + stopid, stream=True) as response:
        # arrivals formatted like <ol class="arrivalsAtStop"><li><strong>5 minutes</strong>
        # concatenate 2 buffers so that we can find tags in the back half of the stream
        iterator = response.iter_content(constants.BUFFSIZE)
        buff[:constants.BUFFSIZE] = next(iterator)
        # have to copy byte by byte rather than vectorized
        for k, this in enumerate(iterator):
            buff[constants.BUFFSIZE:] = this
            tagind = buff.find(b'arrivalsAtStop')
            if (tagind != -1) and (tagind < constants.BUFFSIZE):
                tagind += buff[tagind:].find(b'<strong>') + 8
                timeend = tagind + buff[tagind:].find(b' ')
                rowdata[j] = buff[tagind:timeend].decode()
                if len(rowdata[j]) == 1:
                    rowdata[j] += ' '
                j += 1
                if j == 3:
                    break
            # shift the array
            buff[:constants.BUFFSIZE] = buff[constants.BUFFSIZE:]
            gc.collect()
            
