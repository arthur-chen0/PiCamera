echo remove build and dist.....
rm -rf /home/pi/auto_test/build
rm -rf /home/pi/auto_test/dist

echo generate exe.....
pyinstaller -n camera_test -F /home/pi/auto_test/camera.py

echo remove exe from /usr/local/bin
rm /usr/local/bin/camera_test

echo copy exe to /usr/local/bin
cp /home/pi/auto_test/dist/camera_test /usr/local/bin/
