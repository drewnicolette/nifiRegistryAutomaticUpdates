#!/bin/bash

tar xvzf nipyapi.tgz
cd nipyapi/
sudo python3 setup.py install

sleep 5

#write out current crontab
crontab -l > pullAutomation
echo "*/1 * * * * /usr/bin/python3 ~/registryPullAutomation/registryAutomation.py > /tmp/listener.log 2>&1" >> pullAutomation
crontab pullAutomation
rm mycron