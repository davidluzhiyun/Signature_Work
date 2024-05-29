Initial field test

What is done in the experiment:
Monitor 2 Weight Machines for 24 hours
Send up the data file every 1 hour
Delete local file
The monitor changed to remove files after uploading.


Explanation of Files:
test.py is a test of the new feature of removing local file

monitor.py is a modified version of the monitor3.py in the demo that deletes local files after upload. See it as a homemade library.

Run main.py to start the field test. However, before running don’t forget to:
Change the netid to your own and the passwd to the one you set for your box.
Change the mac address to that of your sensors and the names to names you want for the sensors.
Change the target directory to the one you disire 

Photos and DataCollected are added manually after the test. They contain the photos of the experimental setup and the data collected respectively.


Todo:
Change into event:
Start end time

Threshold should be based noise level (n*std) at beginning
