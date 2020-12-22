
import asyncio
import sys
import threading
import signal
import socket
import psutil
import argparse
import datetime
import traceback
import logging
import logging.config
from loggingConfig import LOGGING
from subprocess import Popen
from time import sleep
from database import db, time_now

parser = argparse.ArgumentParser(description='camera listener.')
parser.add_argument('-p','--path',help='Directory on the server',default='photo')
args = parser.parse_args()

db.setup("asyncio")
test_id = datetime.datetime.today().strftime("%Y%m%d%H%M%S")
start_time = time_now()

# logging.config.fileConfig('logging.conf', defaults={'date':datetime.datetime.now().strftime('%m_%d_%H_%M_%S')})
LOGGING['handlers']['debug']['filename'] = datetime.datetime.now().strftime('listener_%m_%d_%H_%M_%S.log')
LOGGING['handlers']['error']['filename'] = datetime.datetime.now().strftime('listener_error_%m_%d_%H_%M_%S.log')

logging.config.dictConfig(config=LOGGING)
log_c = logging.getLogger('console')
log_d = logging.getLogger('DebugLogger')
log_e = logging.getLogger('ErrorLogger')

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('google.com', 0))
ipaddr = s.getsockname()[0]

def exceptionHandler(e):
    error_class = e.__class__.__name__ #取得錯誤類型
    detail = e.args[0] #取得詳細內容
    cl, exc, tb = sys.exc_info() #取得Call Stack
    lastCallStack = traceback.extract_tb(tb)[-1] #取得Call Stack的最後一筆資料
    fileName = lastCallStack[0] #取得發生的檔案名稱
    lineNum = lastCallStack[1] #取得發生的行號
    funcName = lastCallStack[2] #取得發生的函數名稱
    errMsg = "File \"{}\", line {}, in {}: [{}] {}".format(fileName, lineNum, funcName, error_class, detail)
    loge(errMsg)

def logi(message):
    log_c.info(str(message))
    log_d.info(str(message))

def logd(message):
    log_d.debug(str(message))

def loge(message):
    log_c.error(str(message))
    log_d.error(str(message))
    log_e.error(str(message))

def cameraTask():
    Popen(['python3','camera.py','-s','5','-u','-p',str(args.path)])

def terminateCameraTask():
    for process in psutil.process_iter():
        cmdLine = process.cmdline()
        if 'python3' in cmdLine and 'camera.py' in cmdLine:
            logi('camera task found. Terminating it.')
            process.terminate()
            return  
    logi('camera not found')

def getIpAddress():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('google.com', 0))
    return s.getsockname()[0]

async def getPowerOnTime():
    global ipaddr
    rec = await db.table('cameraAlive').get(str(ipaddr)).run()
    logd(str(rec))
    return int(rec.get('power_on_time'))

async def updateCount(count):
    global ipaddr
    tableData = dict()
    tableData['reboot_Times'] = count
    rec = await db.table('cameraAlive').get(str(ipaddr)).update(tableData)
    logd(str(rec))
    await updateResult(count)
    sleep(1)
    # assert rec['error'] == 0

async def updateResult(count):
    global ipaddr
    rec = await db.table('testResult').get(str(test_id)).run()
    if rec is None:
        tableData = dict()
        tableData['test_id'] = str(test_id)
        tableData['start_time'] = start_time
        tableData['end_time'] = time_now()
        tableData['ip'] = ipaddr
        tableData['reboot_Times'] = count
        rec = await db.table('testResult').insert(tableData)
        logd(str(rec))
        # print(rec)
    else:
        tableData = dict()
        tableData['end_time'] = time_now()
        tableData['reboot_Times'] = count
        rec = await db.table('testResult').get(str(test_id)).update(tableData)
        logd(str(rec))
        # print(rec)
    sleep(1)

    
cameraTimer = None
count = 0
async def changefeed():
    global cameraTimer, count
    preState = False
    currentState = False
    power_on_time = await getPowerOnTime()
    await updateResult(count)

    try:
        changes = await db.table('powerstategit').watch()
        async for change in changes:
            logd("changefeed " + str(change))
            changeStatus = change.get('new_val').get('status',False)
            logi("============================== " + changeStatus + " ==============================")
            preState = currentState

            if 'power on' in changeStatus:
                currentState = True

                t = threading.Thread(target = cameraTask)
                t.start()

                cameraTimer = threading.Timer(power_on_time + 30, terminateCameraTask)
                cameraTimer.start()

            elif 'power off' in changeStatus:
                if cameraTimer is not None:
                    cameraTimer.cancel()
                    cameraTimer = None
                terminateCameraTask()
                # sleep(1)
                # terminateCameraTask() #make sure camera task be terminated
                currentState = False
            else:
                pass

            if(preState and not currentState):
                count += 1
                logi("reboot times: " + str(count))
                await updateCount(count)
    except Exception as exc:
        exceptionHandler(exc)

loop = None
def quit(signum, frame):
    global count,loop
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
    exceptionHandler(exc)

