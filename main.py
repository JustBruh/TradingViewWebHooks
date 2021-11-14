import os
import socket
import json
import requests
import logging
import datetime
import os
import sys

logging.basicConfig(filename="tradingviewrepeater.log", level=logging.INFO)


def is_request_valid(request:dict) -> bool:
    errors = ""

    bot_id_not_exist = "Request does not contain Bot ID"
    side_not_exist = "Request does not contain Side"
    no_trade_not_exist = "Request does not contain no_trade"


    if "bot_id" not in request:
        errors += bot_id_not_exist + "\n"
    if "side" not in request and "no_trade" not in request:
        errors += side_not_exist + " and \n" + no_trade_not_exist
    
    if errors == "":
        return True

    logging.error(errors)

    return False

with open('config.json', 'r',encoding='utf-8') as f:
    config = json.load(f)
    f.close()    

def save_to_json(data):
    with open('data.json', 'w',encoding='utf-8') as f:
        json.dump(data, f)
        f.close()

def need_retrive(current_parameters:dict) -> bool:
    with open('data.json', 'r',encoding='utf-8') as f:
        data = json.load(f)
        f.close()

        bot_id = current_parameters["bot_id"]
        current_parameters.pop("bot_id")
        current_parameters["date_time"] = str(datetime.datetime.now())[:-5] 

        if "no_trade" in current_parameters:
            if current_parameters["no_trade"] == "true":
                current_parameters["processing_result"] = "passed"
                data[bot_id].append(current_parameters)
                save_to_json(data)
                return False

        if data != {}:
            if bot_id not in data:
                current_parameters["processing_result"] = "sent"
                data[bot_id] = [current_parameters]
                save_to_json(data)
                return True

            if data[bot_id] == []:
                current_parameters["processing_result"] = "sent"
                data[bot_id].append(current_parameters)
                save_to_json(data)
                return True

                        
            if current_parameters["side"] != data[bot_id][-1].get("side"):
                current_parameters["processing_result"] = "sent"
                data[bot_id].append(current_parameters)
                save_to_json(data)
                return True
            else:
                current_parameters["processing_result"] = "passed"
                data[bot_id].append(current_parameters)
                save_to_json(data)
                return False

        else:
            current_parameters["processing_result"] = "sent"
            data[bot_id] = [current_parameters]
            save_to_json(data)
            return True

def split_request(request:str) -> bytes:
    header, html = request.split(b'\r\n\r\n', 1)
    return header, html[1:-1]

def run_server():   
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=0)
        server_socket.bind((config["server_host"], int(config["server_port"])))
        server_socket.listen(10)
        with requests.Session() as session:
            while True:
                connection_socket, client_addr = server_socket.accept()
                data = connection_socket.recv(2048)
            
                request_body = split_request(data)[1]
                request_body = str(request_body)[2:-1]
                request_body = request_body.replace('*', "'")
                request_body = request_body.replace("\\n", " ")
                logging.info("Received request body - " + request_body)
    
                request_body = eval("{"+request_body+"}")
                if not is_request_valid(request_body):
                    connection_socket.sendall(b'Request is not valid 400')
                    connection_socket.close()  
                    continue
                else:    
                    connection_socket.sendall(b'Success 200')
    
                request_data = request_body["Keys"]
                endpoint_url = request_body["endpoint"]
                if need_retrive(request_body):
                    response = session.request("POST", endpoint_url, data=request_data, timeout=10)
                    logging.info("Sended request, message - " + request_data + "\n Response - " + response.text)
                
                connection_socket.close()
         
    except KeyboardInterrupt:
        print("Keyboard Interrupt")
        server_socket.close()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    
    except Exception as e:
        logging.error("Exception handled! - " + str(e))

if __name__ == "__main__":
    run_server()