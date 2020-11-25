
import asyncio
import os
import sys
import threading
import signal
import socket
from time import sleep
from database import db, time_now

db.setup("asyncio")

def cameraTask():
    os.system('python3 camera.py -s 5 -p photo2 -u')
    # print('Camera task done')

def terminateCameraTask():
    pid = open("/home/pi/PiCamera/pid.txt")
    cameraPid = pid.readline()
    try:
        os.system("kill -2 " + cameraPid)
    except Exception as e:
        print(e)

def getIpAddress():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('google.com', 0))
    return s.getsockname()[0]

async def getPowerOnTime():
    ipaddr = getIpAddress()
    rec = await db.table('cameraAlive').get(str(ipaddr)).run()
    return int(rec.get('power_on_time'))

async def updateCount(count):
    ipaddr = getIpAddress()
    tableData = dict()
    tableData['reboot_Times'] = count
    rec = await db.table('cameraAlive').get(str(ipaddr)).update(tableData)
    # assert rec['error'] == 0

async def updateResult(count):
    ipaddr = getIpAddress()
    tableData = dict()
    tableData['time'] = time_now()
    tableData['ip'] = ipaddr
    tableData['reboot_Times'] = count
    rec = await db.table('testResult').insert(tableData)

# async def get_connection():
#     return await r.connect(dbSettings.RDB_HOST, dbSettings.RDB_PORT)

# async def changefeed_old():

#     conn = await get_connection()
#     changes = await r.db("picamera").table("camera").changes()["new_val"].run(conn)
#     async for change in changes:
#         print("changefeed_old " + str(change))

# async def changefeed_new():
#     conn = await get_connection()
#     changes = await r.db("picamera").table("camera").changes()["old_val"].run(conn)
#     async for change in changes:
#         print("changefeed_new " + str(change))
cameraTimer = None
count = 0
async def changefeed():
    global cameraTimer, count
    preState = False
    currentState = False
    power_on_time = await getPowerOnTime()

    changes = await db.table('powerstate').watch()
    async for change in changes:
        # print("changefeed " + str(change))
        changeStatus = change.get('new_val').get('status',False)
        print("========================= " + changeStatus + " =========================")
        preState = currentState

        if 'power on' in changeStatus:
            currentState = True

            t = threading.Thread(target = cameraTask)
            t.start()

            cameraTimer = threading.Timer(power_on_time + 30, terminateCameraTask)
            cameraTimer.start()

        elif 'power off' in changeStatus:
            if 'cameraTimer' in locals():
                cameraTimer.cancel()
            terminateCameraTask()
            currentState = False
        else:
            pass

        if(preState and not currentState):
            count += 1
            print("reboot times: " + str(count))
        await updateCount(count)

loop = None
def quit(signum, frame):
    global count,loop
    os.system("python3 /home/pi/PiCamera/updateResult.py -t " + str(count))
    if cameraTimer is not None:
        cameraTimer.cancel()
    loop.close()
    sys.exit(0) 

try:
    signal.signal(signal.SIGINT, quit)
    signal.signal(signal.SIGTERM, quit)

    loop = asyncio.get_event_loop()
    loop.create_task(changefeed())
    loop.run_forever()

except Exception as exc:
        print("Excetption: " + str(exc))

