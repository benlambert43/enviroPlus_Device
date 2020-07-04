# enviroPlus_Device

Device application driver for enviro+ hardware.

driver.py sends data to REST API

NodeJS server used for exporting enviro+ values with a REST API, consumed by https://github.com/benlambert43/enviroPlus_App

# SEE IMG_0020.jpg and DEMO_VIDEO.MP4 !!!


System requirements:
- Node JS
- Python (and python dependencies, which may require manual install.)
- MongoDB (I used MongoDB Atlas here, Raspian is a 32-bit OS which limits the release version of a local MongoDB instance, in this case NodeJS requires a somewhat recent release of MongoDB which was not available on the RPi.)


Starting MongoDB locally: 
sudo systemctl enable mongodb
sudo systemctl start mongodb

Start nodejs server BEFORE running python script.

1) start nodejs server:
node index.js

2) start python driver:
python driver.py
