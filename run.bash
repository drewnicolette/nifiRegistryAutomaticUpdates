#!/bin/bash

#Eventually can pull from .ini
nifiIP=10.11.4.51
bastion_host=bastion
account_name=maintuser

echo ""
echo Sending commands to $nifiIP
scp -r -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o "ProxyJump $bastion_host" registryPullAutomation/ $account_name@$nifiIP:
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -J $bastion_host -T $account_name@$nifiIP '$(cd registryPullAutomation; nohup ./installAutomaticPull.bash >> installAutomaticPull.result 2>&1 &)' > /dev/null 2>&1 &
echo "Commands Sent!"