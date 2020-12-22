import serial
import os
import datetime
from database import db, time_now
from time import sleep

def update(msg):
    data = dict()

    # add some data
    data['time'] = time_now()
    data['status'] = msg
    # print(data)

    ret = db.table('powerstateTest').insert(data)
    # print(ret)
    assert ret['errors'] == 0
    return ret

def countdown(time, power):
    for secs in range(int(time), 0, -1):
        if power:
            print('power on:', secs, end=' \r')
        else:
            print('power off:', secs, end=' \r')
        sleep(1)

# ==============================Main=====================================
 
db.setup()

preState = False
currentState = False
is_set = False
count = 0
power_on_time = 20
power_off_time = 5
try:  
    while (True):

        update('power on')
        countdown(power_on_time, True)
        # sleep(power_on_time)

        update('power off')
        countdown(power_off_time, False)
        # sleep(power_off_time)

        count += 1
        print("reboot times: " + str(count))
  
except KeyboardInterrupt: 
    print("KeyboardInterrupt")
