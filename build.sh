echo remove build and dist.....
rm -rf /home/pi/auto_test/build
rm -rf /home/pi/auto_test/dist

echo generate exe.....
pyinstaller -F /home/pi/auto_test/camera.py

echo remove exe from /usr/local/bin
rm /usr/local/bin/camera

echo copy exe to /usr/local/bin
cp /home/pi/auto_test/dist/camera /usr/local/bin/
