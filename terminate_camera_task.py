import psutil
count = 0
# for process in psutil.process_iter():
#     cmdLine = process.cmdline()
#     if 'python3' in cmdLine :
#         print(cmdLine)
#         uids = process.open_files()
#         print(uids)
#     count+=1
# print(count)

#     cmdLine = process.cmdline()
#     print(cmdLine)
    # if 'python3' in cmdLine and 'camera.py' in cmdLine:
    #     print("Process found")
        # process.terminate()
        # break;
    # else:
    #     print("process not found")


for process in psutil.process_iter():
    cmdLine = process.cmdline()
    if 'python3' in cmdLine and 'camera.py' in cmdLine:
        print('camera task found. Terminating it.')
        process.terminate()
        break
    else:
        pass
    


