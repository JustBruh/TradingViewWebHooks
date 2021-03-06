import os
import socket
import simplejson as json
import requests
import logging
import datetime
import os
import sys
import threading

logging.basicConfig(filename="main.log", level=logging.INFO)

cache = {}
with open('data.json', 'r',encoding='utf-8') as f:
    cache = json.load(f)
    f.close()

with open('config.json', 'r',encoding='utf-8') as f:
    config = json.load(f)
    f.close()  

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

def save_to_json(data):
    with open('data.json', 'w',encoding='utf-8') as f:
        json.dump(data, f)
        f.close()

def need_retrive(current_parameters:dict) -> bool:

        bot_id = current_parameters["bot_id"]
        current_parameters.pop("bot_id")
        current_parameters["date_time"] = str(datetime.datetime.now())[:-5] 

        if "no_trade" in current_parameters:
            if current_parameters["no_trade"] == "true":
                current_parameters["processing_result"] = "passed"
                cache[bot_id].append(current_parameters)
                return False

        if cache != {}:
            if bot_id not in cache:
                current_parameters["processing_result"] = "sent"
                cache[bot_id] = [current_parameters]
                return True

            if cache[bot_id] == []:
                current_parameters["processing_result"] = "sent"
                cache[bot_id].append(current_parameters)
                return True

                        
            if current_parameters["side"] != cache[bot_id][-1].get("side"):
                current_parameters["processing_result"] = "sent"
                cache[bot_id].append(current_parameters)
                return True
            else:
                current_parameters["processing_result"] = "passed"
                cache[bot_id].append(current_parameters)
                return False

        else:
            current_parameters["processing_result"] = "sent"
            cache[bot_id] = [current_parameters]
            return True

def split_request(request:str) -> bytes:
    header, html = request.split(b'\r\n\r\n', 1)
    return header, html[1:-1]

def run_server():   
    try:
        logging.info(str(datetime.datetime.now()) + "    Main.py || Trying to start main.py! - ")
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=0)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
 
        server_socket.bind((config["server_host"], int(config["server_port"])))
        server_socket.listen()

        logging.info(str(datetime.datetime.now()) + "    Main.py || Started main.py! - ")

        with requests.Session() as session:
            while server_socket:

                connection_socket, client_addr = server_socket.accept()
                t = threading.Thread(target=process_client, args=(connection_socket, session))
                t.start()

        server_socket.close()
        logging.info(str(datetime.datetime.now()) + "    Main.py || Server socket closed - ")

    except KeyboardInterrupt:
        print("Keyboard Interrupt")
        save_to_json(cache)
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    except Exception as e:
        logging.error(str(datetime.datetime.now()) + "    Main.py || Exception handled! - " + str(e)) 
        server_socket.close()
        save_to_json(cache)
    except:
        logging.error(str(datetime.datetime.now()) + "    Main.py || Non-standart exception handled! - ")
        save_to_json(cache)


def process_client(connection_socket, requests_session):
    data = connection_socket.recv(2048)

    request_body = split_request(data)[1]
    request_body = str(request_body)[2:-1]
    request_body = request_body.replace('*', "'")
    request_body = request_body.replace("\\n", " ")

    logging.info(str(datetime.datetime.now()) + "    Main.py || Received request body - " + request_body)
    request_body = eval("{"+request_body+"}")

    if not is_request_valid(request_body):
        connection_socket.close()  
        return None
     
    if need_retrive(request_body):
        logging.info(str(datetime.datetime.now()) + " Sended request, message - " + request_body["Keys"])
        response = requests_session.post(request_body["endpoint"], data=request_body["Keys"])
        logging.info(str(datetime.datetime.now()) + " Response - " + response.text)

    save_to_json(cache)
    connection_socket.close


if __name__ == "__main__":
    run_server()