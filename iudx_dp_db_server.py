from flask import Flask, jsonify, request
import pandas as pd
import json
import  configparser

app = Flask(__name__)
server_config = configparser.ConfigParser()
server_config.read('server_config.cfg')

db_server_ip = server_config.get('DB_SERVER', 'ip')
db_server_port = server_config.get('DB_SERVER', 'port')

@app.route("/save_response", methods = ["GET", "POST"])
def save_response():
    if (request.method == "POST"):
        data = json.loads(request.get_data().decode())['response']
        df = pd.DataFrame.from_dict(data, orient='columns')
        df.to_csv('test_response.csv',  index=False) 
        print('saved successfully')
    return "Ok from DB"


if __name__ == '__main__':
    app.run(host=db_server_ip, port=db_server_port, debug=False)
