echo remove build and dist.....
rm -rf /home/pi/PiCamera/build
rm -rf /home/pi/PiCamera/dist

echo generate exe.....
pyinstaller -F /home/pi/PiCamera/camera.py

echo remove exe from /usr/local/bin
rm /usr/local/bin/camera

echo copy exe to /usr/local/bin
cp /home/pi/auto_test/dist/camera /usr/local/bin/
