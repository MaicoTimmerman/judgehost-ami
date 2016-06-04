#!/usr/bin/env python
from __future__ import print_function
import boto.ec2
import sys

import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# From http://cloud-images.ubuntu.com/locator/ec2/
# Choose the hvm:ebs-ssd "Instance Type" for say trusty us-east
# BASEAMI = 'ami-fdb9fc98'  # Trusty 14.04 amd64 hvm:ebs-ssd 2015-09-28
# baseami = 'ami-5c207736'  # Trusty 14.04 amd64 hvm:ebs-ssd 2015-12-18
# BASEAMI = 'ami-f95ef58a'  # ubuntu-trusty-14.04-amd64-server-20160114.5
BASEAMI = 'ami-3079f543'  # ubuntu-trusty-14.04-amd64-server-20160114.5  HVMSSD
REGION = 'eu-west-1'
# ssh_keypair = 'domjudge-aws'
# ssh_securitygroup = 'open-ssh'

# poweroff or reboot system after finished
# default: none
#
# power_state can be used to make the system shutdown, reboot or
# halt after boot is finished.  This same thing can be acheived by
# user-data scripts or by runcmd by simply invoking 'shutdown'.
#
# Doing it this way ensures that cloud-init is entirely finished with
# modules that would be executed, and avoids any error/log messages
# that may go to the console as a result of system services like
# syslog being taken down while cloud-init is running.
#
# If you delay '+5' (5 minutes) and have a timeout of
# 120 (2 minutes), then the max time until shutdown will be 7 minutes.
# cloud-init will invoke 'shutdown +5' after the process finishes, or
# when 'timeout' seconds have elapsed.
#
# delay: form accepted by shutdown.  default is 'now'. other format
#        accepted is +m (m in minutes)
# mode: required. must be one of 'poweroff', 'halt', 'reboot'
# message: provided as the message argument to 'shutdown'. default is none.
# timeout: the amount of time to give the cloud-init process to finish
#          before executing shutdown.
# condition: apply state change only if condition is met.
#            May be boolean True (always met), or False (never met),
#            or a command string or list to be executed.
#            command's exit code indicates:
#               0: condition met
#               1: condition not met
#            other exit codes will result in 'not met', but are reserved
#            for future use.
#
CCONFIG = """#cloud-config
power_state:
  mode: reboot
  timeout: 900
  condition: True
"""

UDSCRIPT = """#!/bin/bash -ex

# install needed packages for ansible
sudo apt-get update
sudo apt-get install -y -q software-properties-common git-core
sudo apt-add-repository -y ppa:ansible/ansible
sudo apt-get update
sudo apt-get install -y -q ansible

sudo ansible-pull -U http://github.com/MaicoTimmerman/judgehost-ami.git -d /mnt/playbooks -i "localhost,"

exit 0
"""  # noqa

combined_message = MIMEMultipart()
sub_message = MIMEText(CCONFIG, "cloud-config", sys.getdefaultencoding())
sub_message.add_header('Content-Disposition',
                       'attachment; filename="00cloudconfig.txt"')
combined_message.attach(sub_message)

sub_message = MIMEText(UDSCRIPT, "x-shellscript", sys.getdefaultencoding())
sub_message.add_header('Content-Disposition',
                       'attachment; filename="01bootstrap.txt"')
combined_message.attach(sub_message)

conn = boto.ec2.connect_to_region(REGION)
reservation = conn.run_instances(
    BASEAMI,
    # key_name=ssh_keypair,
    # security_groups=[ssh_securitygroup],
    instance_type='t2.micro',
    user_data=combined_message.as_string()
)
instance = reservation.instances[0]

print("Waiting for instance to boot", end='')
while instance.state != 'running':
    print(".", end='')
    sys.stdout.flush()
    time.sleep(2)
    instance.update()
print()

print("Instance provisioning...")
print("Waiting for instance to stop")
while instance.state != 'stopped':
    print(".", end='')
    sys.stdout.flush()
    time.sleep(5)
    instance.update()
print()
print("instance stopped and is ready")

# ts = int(time.time())
# newami_id = conn.create_image(instance.id, "DOMjudge-judgehost-{0}".format(ts), description="DOMjudge Judgehost {0}".format(ts))
# instance.terminate()
#
# print("DOMjudge Judgehost Created")
# print("AMI ID: " + newami_id)
#
# print("Waiting for image creation to finish")
# image = conn.get_all_images(image_ids=[newami_id])[0]
# while image.state == 'pending':
#     print(".", end='')
#     sys.stdout.flush()
#     time.sleep(5)
#     image.update()
# if image.state == 'available':
#     print("Image created successfully!")
#     print("AMI ID: " + newami_id)
# else:
#     print("Error creating image. Check AWS console for details")
