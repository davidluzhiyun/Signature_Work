
import monitor
from monitor import Monitor
from ftplib import FTP_TLS

ftps = FTP_TLS('ftp.box.com')
# login after securing control channel
ftps.login("netid","passwd")     
# switch to secure data connection.. 
# IMPORTANT! Otherwise, only the user and password is encrypted and
# not all the file data.
ftps.prot_p()
#open the directory
ftps.cwd('/SmartGymData')

# MACs and names
a =[['d6:3e:9f:34:9e:1a','Alex']]
m = Monitor(a)

# parameters for sampling frequency and range
m.watch_start_config()

# number of cycles to run. change to while true for long term
for i in range(1):

    m.watch_start()

    # length of each cycle in seconds
    m.watching_for(10.0)

    m.watch_end()
    m.upload(ftps)
m.quit_reset()
ftps.quit()