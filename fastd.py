# This file is managed by ansible, don't make changes here - they will be overwritten.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author:
#   dray <dresen@itsecteam.ms>
#
# Script to count fastd connections adapted from
# https://github.com/FreiFunkMuenster/gateway-ffms/blob/master/nrpe/check_fastd_connections.py
#
# About this plugin:
#   This plugin collects the number of fastd connection for FFMS
#
# Configuration
#
# <Module fastd>
#     server_address "/tmp/fastd-status"
# </Module>
# 
# for multiple fastd instances, add each socket to server_address seperated by :
# Example:
# server_address "/tmp/fastd-a-status:/tmp/fastd-b-status"
#
#

import collectd
import socket
import sys
import json
import glob

server_address = ''


def read(data=None):
    vl = collectd.Values(type='gauge')
    vl.plugin='fastd_connections'


    try:
        servers = server_address.split(":")
        for server in servers:
            connections = 0    
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(server)

            received_count = 1
            received_data = ""

            while received_count > 0:
                data = sock.recv(1024)
                received_count = len(data)
                received_data += data;

            sock.close();
        
            received_json = json.loads(received_data);

            for item in received_json["peers"]:
                p = received_json["peers"][item]
                if p["connection"]:
                    connections += 1
            vl.type_instance = server.split('/')[-1] 
            vl.dispatch(values=[connections])
        
    except socket.error, msg:
        collectd.error("[ffbs Fastd] Socket read failed: %s" % (msg))
        # vl.dispatch(values=[-1])    
    

def write(vl, data=None):
    for i in vl.values:
        print "%s (%s): %f" % (vl.plugin, vl.type, i)

def config (config):
    global server_address
    server_address = ''   #'/tmp/fastd-status'

    for node in config.children:
        key = node.key.lower()
        val = node.values[0]

        if key == 'server_address':
            server_address = val
            if server_address == '':
                server_address = glob.glob('/tmp/fastd*.socket')

        else:
            collectd.warning("ffbs_fastd plugin: Unknown configuration key: %s." % key )
            continue

    if server_address == '':
        collectd.error('ffbs_fastd plugin: No Serveradress configured.' )
    else:
        collectd.info("ffbs_fastd plugin: Successful configured with server_address %s." % server_address)
    
collectd.register_read(read);
collectd.register_write(write);
collectd.register_config(config);
