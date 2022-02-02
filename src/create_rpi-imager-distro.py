#!/usr/bin/python3
import pysftp
from tempfile import TemporaryDirectory, mktemp
import json
import os
import io
import yaml

# Example output: https://unofficialpi.org/rpi-imager/rpi-imager-octopi-klipper.json

def get_folder_json(sftp, folder, max_count, is_nightly=False):
    return_value = []
    count = max_count
    with TemporaryDirectory() as temp_dir:
        with sftp.cd(folder):             # temporarily chdir to public
            for file_path_basename in sftp.listdir():
                file_full_path = distro_folder + "/" + file_path_basename
                if file_path_basename.endswith(".json"):
                    count -= 1
                    if count < 0:
                        return
                    
                    print(file_path_basename)
                    sftp.get(file_path_basename, localpath=os.path.join(temp_dir, file_path_basename))
        
        for file_path in os.listdir(temp_dir):
            full_path = os.path.join(temp_dir, file_path)
            json_data = None
            with open(full_path) as f:
                json_data = json.load(f)
            return_value.append(json_data)
            date_stamp = file_path.split("_")[0]
            if is_nightly:
                json_data["name"] += " (Nightly)"
            else:
                json_data["name"] += " (Stable)"
            json_data["url"] = url + folder + "/" + date_stamp + "_" + json_data["url"]
            # os.system("ls -l " + temp_dir)

    return return_value

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(add_help=True, description='Generate per os the rpi-imager distro json file')
    parser.add_argument('distro_name', help='The distro name')
    args = parser.parse_args()
    
    # distro_name = "FullPageOS"
    distro_name = args.distro_name
    
    distro_folder = "/Distros/" + distro_name
    nightly = distro_folder + "/" + "nightly"

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
        
    with pysftp.Connection(hostname, username=username, password=password) as sftp:
        os_list = get_folder_json(sftp, distro_folder, 1) + get_folder_json(sftp, nightly, 2, True)
        
        output_json = {"os_list": os_list}
        
        tmp_file =  mktemp(suffix=".json")
            
        with open(tmp_file, "w") as w:
            json.dump(output_json, w, indent=2)
        # import code; code.interact(local=dict(globals(), **locals())) 
        
        if sftp.isfile(json_list_output_path):
            sftp.remove(json_list_output_path)
        sftp.put(tmp_file, remotepath=json_list_output_path)
            
        os.unlink(tmp_file)
        
        
        # get_folder_json(sftp, distro_folder, 3)
        
        
        
        
    
