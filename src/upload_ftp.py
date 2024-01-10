#!/usr/bin/env python3
from __future__ import division
import ftplib
import os
import sys
import time
import socket
import paramiko

from configparser import ConfigParser
from collections import OrderedDict

def ini_to_dict(path):
    """

    Read an ini path in to a dict
    :param path: Path to file
    :return: an OrderedDict of that path ini data
    """
    config = ConfigParser()
    config.read(path)
    return_value = OrderedDict()
    for section in reversed(config.sections()):
        return_value[section] = OrderedDict()
        section_tuples = config.items(section)
        for item_turple in reversed(section_tuples):
            return_value[section][item_turple[0]] = item_turple[1]
    return return_value


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.ini")


def get_config():
    return ini_to_dict(CONFIG_PATH)


def viewBar(a,b):
    # original version
    res = a/int(b)*100
    sys.stdout.write('\rComplete precent: %.2f %%' % (res))
    sys.stdout.flush()

def tqdmWrapViewBar(*args, **kwargs):
    try:
        from tqdm import tqdm
    except ImportError:
        # tqdm not installed - construct and return dummy/basic versions
        class Foo():
            @classmethod
            def close(*c):
                pass
        return viewBar, Foo
    else:
        pbar = tqdm(*args, **kwargs)  # make a progressbar
        last = [0]  # last known iteration, start at 0
        def viewBar2(a, b):
            pbar.total = int(b)
            pbar.update(int(a - last[0]))  # update pbar with increment
            last[0] = a  # update last known iteration
        return viewBar2, pbar  # return callback, tqdmInstance


if __name__ == "__main__":
    settings = get_config()
    server=settings["main"]["server"]
    username=settings["main"]["username"]
    password=settings["main"]["password"]
    FileName=sys.argv[1]
    Directory=sys.argv[2]
    tmp_dir = "/tmp"
    filename = FileName
    
    tries = 0
    done = False
    
    print("Uploading " + str(filename) + " to " + str(Directory), flush=True)
    print("Upload to temp folder", flush=True)
    
    while tries < 50 and not done:
        try:
            tries += 1
            transport = paramiko.Transport((server, 22))
            transport.connect(username=username, password=password)
            cbk, pbar = tqdmWrapViewBar(ascii=True, unit='b', unit_scale=True)
            sftp = paramiko.SFTPClient.from_transport(transport)
            path = os.path.join(tmp_dir ,os.path.basename(filename))
            sftp.put(filename, path, callback=cbk)
            dest = os.path.join(Directory, os.path.basename(filename))
            print(path,dest)
            sftp.posix_rename(path, dest)
            done = True
        except IndexError:
            print("Got exception")
            sftp.close()
            transport.close()

            time.sleep(30)
            
    if done == False:
        print("Fail to upload")
        sys.exit(1)        
    print("Done")

    
