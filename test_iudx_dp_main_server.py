import json, requests
import scripts.utilities as utils
import pandas as pd


# necessary file reads
config_file_name = "testConfigs/spatioDP.json"
config = utils.read_config(config_file_name) 
# data = utils.read_data(config["data_file"])


url = 'http://192.168.0.127:11001/process_dp'
data = {
    'config': config
}
response = requests.post(url, data=json.dumps(data))

print("response status: To be configured")