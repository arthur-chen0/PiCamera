import argparse
import socket
from database import db, time_now

parser = argparse.ArgumentParser(description='update test result.')
parser.add_argument('-t', '--times', type=int, default='0',help='test times')

def getIpAddress():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('google.com', 0))
    return s.getsockname()[0]

args = parser.parse_args()
print("Update test result to DB")

db.setup()

ipaddr = getIpAddress()
tableData = dict()
tableData['time'] = time_now()
tableData['ip'] = ipaddr
tableData['reboot_Times'] = args.times
rec = db.table('testResult').insert(tableData)
print(rec)