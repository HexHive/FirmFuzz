#!/bin/bash
user=`whoami`
sudo chown -R $user:$user $1
