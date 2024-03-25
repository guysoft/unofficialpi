#!/usr/bin/python3
import pysftp
from tempfile import TemporaryDirectory, mktemp
import json
import os
import io
import yaml

DEVICES_ALL = [
    "pi1-32bit",
    "pi2-32bit",
	"pi3-32bit",
	"pi3-64bit",
	"pi4-32bit",
	"pi4-64bit",
	"pi5-32bit",
	"pi5-64bit"
]

DEVICES_ARM64 = [
	"pi3-64bit",
	"pi4-64bit",
	"pi5-64bit"
]

# Example output: https://unofficialpi.org/rpi-imager/rpi-imager-octopi-klipper.json

def get_folder_json(sftp, tmp_prefix, folder, arch, max_count, is_nightly=False):
    return_value = []
    count = max_count
    if not sftp.exists(folder):
        print("Skipping non-existent folder: " + str(folder))
        return return_value
    with TemporaryDirectory(dir=tmp_prefix) as temp_dir:
        print("Checking folder: " + str(folder))
        with sftp.cd(folder):             # temporarily chdir to public
            remote_files = [x.filename for x in sorted(sftp.listdir_attr(), key = lambda f: f.st_mtime, reverse=True)]
            for file_path_basename in remote_files:
                file_full_path = distro_folder + "/" + file_path_basename
                if file_path_basename.endswith(".json"):
                    count -= 1
                    if count < 0:
                        break
                    
                    print(file_path_basename)
                    sftp.get(file_path_basename, localpath=os.path.join(temp_dir, file_path_basename))
        for file_path in sorted(os.listdir(temp_dir), reverse=True):
            full_path = os.path.join(temp_dir, file_path)
            json_data = None
            with open(full_path) as f:
                json_data = json.load(f)
            return_value.append(json_data)
            date_stamp = file_path.split("_")[0]
            if is_nightly:
                print(json_data["name"])
                json_data["name"] += " (Nightly)"
            else:
                json_data["name"] += " (Stable)"

            # Handle device list
            devices_list = DEVICES_ALL
            if arch == "arm64" or "64-bit" in json_data["name"]:
                devices_list = DEVICES_ARM64

            if "devices" not in json_data:
                json_data["devices"] = devices_list

            json_data["url"] = url + folder + "/" + date_stamp + "_" + json_data["url"]

            # inject init format
            json_data["init_format"] = "systemd"
            # os.system("ls -l " + temp_dir)

    return return_value

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(add_help=True, description='Generate per os the rpi-imager distro json file')
    parser.add_argument('distro_name', help='The distro name')
    args = parser.parse_args()
    
    # distro_name = "FullPageOS"
    distro_name = args.distro_name

    if "/" in distro_name:
        print("Path detected. Extracting name from path")
        # Example: /Distros/OctoPi/nightly
        # Example2 : /Distros/OctoPi/nightly
        path_data = distro_name.split("/")
        if len(path_data) < 3:
            print(f"Error: the distro path provided is not the one expected: {distro_name}")
        distro_name = distro_name.split("/")[2]
    
    distro_folder = "/Distros/" + distro_name
    nightly = distro_folder + "/" + "nightly"

    nightly64 = distro_folder + "/" + "nightly-arm64"

    json_list_output_path = "/rpi-imager/rpi-imager-" + distro_name.lower() + ".json"
    
    settings = None
    DIR = os.path.dirname(__file__)
    with open(os.path.join(DIR, "config.yaml")) as f:
        try:
            settings = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(exc)
    
    hostname = settings["sftp"]["hostname"]
    username = settings["sftp"]["username"]
    password = settings["sftp"]["password"]
    url = settings["web"]["url"]
    tmp_prefix = settings["io"]["tmp"]
    if tmp_prefix == "default":
        tmp_prefix = None
        
    with pysftp.Connection(hostname, username=username, password=password) as sftp:
        os_list = \
            get_folder_json(sftp, tmp_prefix, distro_folder, None, 1) + \
                get_folder_json(sftp, tmp_prefix, nightly, None, 2, True) + \
                    get_folder_json(sftp, tmp_prefix, nightly64, "arm64", 2, True)
        
        output_json = {"os_list": os_list}
        
        tmp_file =  mktemp(suffix=".json", dir=tmp_prefix)
            
        with open(tmp_file, "w") as w:
            json.dump(output_json, w, indent=2)
        # import code; code.interact(local=dict(globals(), **locals())) 
        
        if sftp.isfile(json_list_output_path):
            sftp.remove(json_list_output_path)
        sftp.put(tmp_file, remotepath=json_list_output_path)
        
        os.unlink(tmp_file)
        
        
        # get_folder_json(sftp, tmp_prefix, distro_folder, 3)
        
        
        
        
    
