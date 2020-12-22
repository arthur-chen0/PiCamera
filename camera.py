#!/usr/bin/python3
import picamera
import time
import argparse
import datetime
import os
import signal
import sys
import threading
import socket
from threading import Condition
from database import db, time_now

parser = argparse.ArgumentParser(description='Auto capture.')
parser.add_argument('-s', '--sleep', type=int, default='3',help='Interval')
parser.add_argument('-t', '--time',type=int, help='Capture Times')
parser.add_argument('-v',help='recording',action='store_true')
parser.add_argument('-vt',help='recording X sec', type=int)
parser.add_argument('-p','--path',help='Directory on the server',default='photo')
parser.add_argument('-r',nargs=2, type=int, default=[280,180], help='resolution')
parser.add_argument('-b', '--brightness', help='camera brightness', type=int, default='55')
parser.add_argument('-a', '--rotation', help='camera rotation angle(0-360)', type=int, default='0')
parser.add_argument('-u',help='update state to DB',action='store_true')

args = parser.parse_args()
condition = threading.Condition()
camera = picamera.PiCamera() 
camera.brightness = args.brightness
camera.rotation = args.rotation
path = os.path.abspath('/home/pi/PiCamera/photo')
ipaddr = None

if not os.path.exists(path):
    print(str(path) + " is not exist, make it.")
    os.makedirs(path)

print("\nVersion: 1.2 \n")
print("Ctrl + C to force stop capture or recording!!\n")
print("Directory on the server " + args.path)
print("resolution: " + str(args.r[0]) + " * " + str(args.r[1]))

def getPid():
    pid = os.getpid()
    fileName = "/home/pi/PiCamera/pid.txt"
    cameraPid = open(fileName, "w")
    cameraPid.writelines(str(pid))
    cameraPid.close()

def countdown(sleepTime):
    for secs in range(sleepTime, 0, -1):
        print('sleep ', secs, end=' \r')
        time.sleep(1)
    print("          ")

firstCap = False
def capture():
    global firstCap
    countdown(args.sleep)
    date = datetime.datetime.today().strftime("%m_%d_%H_%M_%S")
    if not firstCap:
        date = date + "_on" # this is for image web filtering
    pictureName = path + "/" + str(date) + ".jpg"
    print("Take picture: " + pictureName)
    camera.resolution = (args.r[0], args.r[1])
    camera.capture(pictureName)
    copyPictureToServer(pictureName)

    if not firstCap:
        firstCap = True

    if args.u:
        updateStateToServer()

def recording():
    condition.acquire()
    print("Start recording...")
    date = datetime.datetime.today().strftime("%m_%d_%H_%M_%S")
    videoName = path + "/" +str(date) + ".mjpeg"
    camera.resolution = (args.r[0], args.r[1])
    camera.start_recording(videoName)
    if(args.vt == None):
        condition.wait()
    else:
        print("recording " + str(args.vt) + " sec...")
        camera.wait_recording(args.vt)
        camera.stop_recording()
        copyVideoToServer()
        sys.exit(0)

def copyPictureToServer(pictureName):
    os.system("scp " + pictureName + " jhtrd@192.168.70.187:/home/jhtrd/auto_test/photo_web/" + args.path)
    os.system("rm " + path + "/*.jpg")

def copyVideoToServer():
    os.system("scp " + path + "/*.mjpeg" + " jhtrd@192.168.70.187:/home/jhtrd/auto_test/video/")
    os.system("rm " + path + "/*.mjpeg")

def updateStateToServer():
    data = dict()
    data['ip'] = str(ipaddr)
    data['date'] = time_now()
    data['capture'] = 'on'
    rec = db.table('cameraAlive').get(str(ipaddr)).update(data)

def getIpAddress():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('google.com', 0))
    return s.getsockname()[0]

def quit(signum, frame):
    if args.v:
        condition.acquire()
        print("Stop recording!!")
        condition.notify()
        condition.release()
        camera.stop_recording()
        copyVideoToServer()
        
    else:
        # print("  Stop capture!!")
        camera.close()

    sys.exit(0)  

# ================================ Main ================================
try:
    signal.signal(signal.SIGINT, quit)
    signal.signal(signal.SIGTERM, quit)
    # getPid()
    db.setup()
    ipaddr = getIpAddress()

    if args.v or args.vt != None:
        recording()
    else:
        if args.time == None:
            print("Capture while loop\n")
            while True:
                capture()
            
        else:
            print("Capture " + str(args.time) + " times\n")
            for i in range(args.time):
                capture()
            camera.close()

except Exception as exc:
        print(exc)

