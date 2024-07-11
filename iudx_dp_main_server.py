from flask import Flask, jsonify, request
from iudx_dp_main_process import main_process
import scripts.utilities as utils
import json
import requests
import  configparser

app = Flask(__name__)
server_config = configparser.ConfigParser()
server_config.read('server_config.cfg')


main_server_ip = server_config.get('MAIN_SERVER', 'ip')
main_server_port = server_config.get('MAIN_SERVER', 'port')
db_server_ip = server_config.get('DB_SERVER', 'ip')
db_server_port = server_config.get('DB_SERVER', 'port')


def send_response(response):
    url = 'http://'+db_server_ip+':'+db_server_port+'/save_response'
    output = {
        'response': response.to_dict()
    }
    r = requests.post(url, data=json.dumps(output, default=str))
    return "Ok"


@app.route("/test_server", methods = ["GET"])
def test_server():
    if (request.method == "GET"):
        data = "Test Server"
        return jsonify({'data': data})

@app.route("/process_dp", methods = ["GET", "POST"])
def process_dp():
    if (request.method == "POST"):
        try:
            config = json.loads(request.get_data().decode())['config']
            operations = utils.oop_handler(config)
            data = main_process(config, operations)
            # response = jsonify(data.to_dict()) #TODO: Post this to other end point to save or process the data further
            send_response(response=data)
        except Exception as e:
            print(e)
    return "Ok from Main Server"

if __name__ == '__main__':
    app.run(host=main_server_ip, port=main_server_port, debug=False)
