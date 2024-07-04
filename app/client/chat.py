import base64
import os
import json
import uuid
import logging
from queue import Queue
import threading
import socket
from datetime import datetime


class CommunicationThread(threading.Thread):
    def __init__(self, chat_queues, target_address, target_port):
        self.chat_queues = chat_queues
        self.chat = {}
        self.target_address = target_address
        self.target_port = target_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.target_address, self.target_port))
        threading.Thread.__init__(self)

    def transmit_message(self, message):
        try:
            self.sock.sendall(message.encode())
            response = ""
            while True:
                data = self.sock.recv(1024)
                print("Received from server:", data)
                if data:
                    response += data.decode()
                    if response.endswith("\r\n\r\n"):
                        print("End of message")
                        return json.loads(response)
        except:
            self.sock.close()
            return {"status": "ERROR", "message": "Transmission Failed"}

    def add_message(self, message):
        recipient = message["msg_to"]
        try:
            self.chat[recipient].put(message)
        except KeyError:
            self.chat[recipient] = Queue()
            self.chat[recipient].put(message)


class Chat:
    def __init__(self):
        self.sessions = {}
        self.users = {
            "messi": {
                "name": "Lionel Messi",
                "country": "Argentina",
                "password": "surabaya",
                "incoming": {},
                "outgoing": {},
            },
            "henderson": {
                "name": "Jordan Henderson",
                "country": "England",
                "password": "surabaya",
                "incoming": {},
                "outgoing": {},
            },
            "lineker": {
                "name": "Gary Lineker",
                "country": "England",
                "password": "surabaya",
                "incoming": {},
                "outgoing": {},
            },
        }
        self.realms = {}

    def process_request(self, data):
        parts = data.split(" ")
        try:
            command = parts[0].strip()
            if command == "authenticate":
                username = parts[1].strip()
                password = parts[2].strip()
                logging.warning("AUTH: authenticate {} {}".format(username, password))
                return self.authenticate_user(username, password)

            if command == "register":
                username = parts[1].strip()
                password = parts[2].strip()
                name = parts[3].strip()
                country = parts[4].strip()
                logging.warning("REGISTER: register {} {}".format(username, password))
                return self.register_user(username, password, name, country)

            # ===================== Intra-server Communication =====================
            elif command == "message":
                session_id = parts[1].strip()
                recipient = parts[2].strip()
                message_content = " ".join(parts[3:])
                sender = self.sessions[session_id]["username"]
                logging.warning(
                    "MESSAGE: session {} send message from {} to {}".format(
                        session_id, sender, recipient
                    )
                )
                return self.send_message(session_id, sender, recipient, message_content)

            elif command == "message_group":
                session_id = parts[1].strip()
                recipients = parts[2].strip().split(",")
                message_content = " ".join(parts[3:])
                sender = self.sessions[session_id]["username"]
                logging.warning(
                    "MESSAGE_GROUP: session {} send message from {} to {}".format(
                        session_id, sender, recipients
                    )
                )
                return self.send_group_message(session_id, sender, recipients, message_content)

            elif command == "inbox":
                session_id = parts[1].strip()
                username = self.sessions[session_id]["username"]
                logging.warning("INBOX: {}".format(session_id))
                return self.get_inbox(username)

            elif command == "send_file":
                session_id = parts[1].strip()
                recipient = parts[2].strip()
                file_path = parts[3].strip()
                encoded_file = parts[4].strip()
                sender = self.sessions[session_id]["username"]
                logging.warning(
                    "SEND_FILE: session {} send file from {} to {}".format(
                        session_id, sender, recipient
                    )
                )
                return self.send_file(session_id, sender, recipient, file_path, encoded_file)

            elif command == "send_group_file":
                session_id = parts[1].strip()
                recipients = parts[2].strip().split(",")
                file_path = parts[3].strip()
                encoded_file = parts[4].strip()
                sender = self.sessions[session_id]["username"]
                logging.warning(
                    "SEND_GROUP_FILE: session {} send file from {} to {}".format(
                        session_id, sender, recipients
                    )
                )
                return self.send_group_file(session_id, sender, recipients, file_path, encoded_file)

            # ===================== Inter-server Communication =====================
            elif command == "add_realm":
                realm_id = parts[1].strip()
                realm_address = parts[2].strip()
                realm_port = int(parts[3].strip())
                return self.add_realm(realm_id, realm_address, realm_port, data)

            elif command == "receive_realm":
                realm_id = parts[1].strip()
                realm_address = parts[2].strip()
                realm_port = int(parts[3].strip())
                return self.receive_realm(realm_id, realm_address, realm_port, data)

            elif command == "message_private_realm":
                session_id = parts[1].strip()
                realm_id = parts[2].strip()
                recipient = parts[3].strip()
                message_content = " ".join(parts[4:])
                sender = self.sessions[session_id]["username"]
                logging.warning(
                    "MESSAGE_PRIVATE_REALM: session {} send message from {} to {} in realm {}".format(
                        session_id, sender, recipient, realm_id
                    )
                )
                return self.send_realm_message(session_id, realm_id, sender, recipient, message_content, data)

            elif command == "send_file_realm":
                session_id = parts[1].strip()
                realm_id = parts[2].strip()
                recipient = parts[3].strip()
                file_path = parts[4].strip()
                encoded_file = parts[5].strip()
                sender = self.sessions[session_id]["username"]
                logging.warning(
                    "SEND_FILE_REALM: session {} send file from {} to {} in realm {}".format(
                        session_id, sender, recipient, realm_id
                    )
                )
                return self.send_file_realm(session_id, realm_id, sender, recipient, file_path, encoded_file, data)

            elif command == "receive_file_realm":
                session_id = parts[1].strip()
                realm_id = parts[2].strip()
                recipient = parts[3].strip()
                file_path = parts[4].strip()
                encoded_file = parts[5].strip()
                sender = self.sessions[session_id]["username"]
                logging.warning(
                    "RECEIVE_FILE_REALM: session {} send file from {} to {} in realm {}".format(
                        session_id, sender, recipient, realm_id
                    )
                )
                return self.receive_file_realm(session_id, realm_id, sender, recipient, file_path, encoded_file, data)

            elif command == "receive_private_realm_message":
                sender = parts[1].strip()
                realm_id = parts[2].strip()
                recipient = parts[3].strip()
                message_content = " ".join(parts[4:])
                logging.warning(
                    "RECEIVE_PRIVATE_REALM_MESSAGE: receive message from {} to {} in realm {}".format(
                        sender, recipient, realm_id
                    )
                )
                return self.receive_realm_message(realm_id, sender, recipient, message_content, data)

            elif command == "message_group_realm":
                session_id = parts[1].strip()
                realm_id = parts[2].strip()
                recipients = parts[3].strip().split(",")
                message_content = " ".join(parts[4:])
                sender = self.sessions[session_id]["username"]
                logging.warning(
                    "MESSAGE_GROUP_REALM: session {} send message from {} to {} in realm {}".format(
                        session_id, sender, recipients, realm_id
                    )
                )
                return self.send_group_realm_message(session_id, realm_id, sender, recipients, message_content, data)

            elif command == "send_group_file_realm":
                session_id = parts[1].strip()
                realm_id = parts[2].strip()
                recipients = parts[3].strip().split(",")
                file_path = parts[4].strip()
                encoded_file = parts[5].strip()
                sender = self.sessions[session_id]["username"]
                logging.warning(
                    "SEND_GROUP_FILE_REALM: session {} send file from {} to {} in realm {}".format(
                        session_id, sender, recipients, realm_id
                    )
                )
                return self.send_group_file_realm(session_id, realm_id, sender, recipients, file_path, encoded_file, data)

            elif command == "receive_group_file_realm":
                session_id = parts[1].strip()
                realm_id = parts[2].strip()
                recipients = parts[3].strip().split(",")
                file_path = parts[4].strip()
                encoded_file = parts[5].strip()
                sender = self.sessions[session_id]["username"]
                logging.warning(
                    "RECEIVE_GROUP_FILE_REALM: session {} send file from {} to {} in realm {}".format(
                        session_id, sender, recipients, realm_id
                    )
                )
                return self.receive_group_file_realm(session_id, realm_id, sender, recipients, file_path, encoded_file, data)

            elif command == "receive_group_realm_message":
                sender = parts[1].strip()
                realm_id = parts[2].strip()
                recipients = parts[3].strip().split(",")
                message_content = " ".join(parts[4:])
                logging.warning(
                    "RECEIVE_GROUP_REALM_MESSAGE: send message from {} to {} in realm {}".format(
                        sender, recipients, realm_id
                    )
                )
                return self.receive_group_realm_message(realm_id, sender, recipients, message_content, data)

            elif command == "fetch_realm_inbox":
                session_id = parts[1].strip()
                realm_id = parts[2].strip()
                username = self.sessions[session_id]["username"]
                logging.warning(
                    "FETCH_REALM_INBOX: {} from realm {}".format(session_id, realm_id)
                )
                return self.get_realm_inbox(username, realm_id)

            elif command == "fetch_realm_chat":
                realm_id = parts[1].strip()
                username = parts[2].strip()
                logging.warning("FETCH_REALM_CHAT: from realm {}".format(realm_id))
                return self.get_realm_chat(realm_id, username)

            elif command == "logout":
                return self.logout()
            elif command == "info":
                return self.info()
            else:
                print(command)
                return {"status": "ERROR", "message": "Invalid Protocol"}
        except KeyError:
            return {"status": "ERROR", "message": "Information not found"}
        except IndexError:
            return {"status": "ERROR", "message": "Invalid Protocol"}

    def authenticate_user(self, username, password):
        if username not in self.users:
            return {"status": "ERROR", "message": "User Not Found"}
        if self.users[username]["password"] != password:
            return {"status": "ERROR", "message": "Incorrect Password"}
        token_id = str(uuid.uuid4())
        self.sessions[token_id] = {
            "username": username,
            "user_detail": self.users[username],
        }
        return {"status": "OK", "token_id": token_id}

    def register_user(self, username, password, name, country):
        if username in self.users:
            return {"status": "ERROR", "message": "User Already Exists"}
        name = name.replace("_", " ")
        self.users[username] = {
            "name": name,
            "country": country,
            "password": password,
            "incoming": {},
            "outgoing": {},
        }
        token_id = str(uuid.uuid4())
        self.sessions[token_id] = {
            "username": username,
            "user_detail": self.users[username],
        }
        return {"status": "OK", "token_id": token_id}

    def get_user(self, username):
        if username not in self.users:
            return False
        return self.users[username]

    def send_message(self, session_id, sender, recipient, message_content):
        if recipient not in self.users:
            return {"status": "ERROR", "message": "Recipient Not Found"}
        self.users[recipient]["incoming"][str(uuid.uuid4())] = {
            "sender": sender,
            "message": message_content,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.users[sender]["outgoing"][str(uuid.uuid4())] = {
            "recipient": recipient,
            "message": message_content,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        return {"status": "OK"}

    def send_group_message(self, session_id, sender, recipients, message_content):
        for recipient in recipients:
            if recipient not in self.users:
                return {"status": "ERROR", "message": "Recipient {} Not Found".format(recipient)}
            self.users[recipient]["incoming"][str(uuid.uuid4())] = {
                "sender": sender,
                "message": message_content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        self.users[sender]["outgoing"][str(uuid.uuid4())] = {
            "recipients": recipients,
            "message": message_content,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        return {"status": "OK"}

    def get_inbox(self, username):
        if username not in self.users:
            return {"status": "ERROR", "message": "User Not Found"}
        return {"status": "OK", "inbox": self.users[username]["incoming"]}

    def send_file(self, session_id, sender, recipient, file_path, encoded_file):
        if recipient not in self.users:
            return {"status": "ERROR", "message": "Recipient Not Found"}
        file_data = base64.b64decode(encoded_file)
        file_name = os.path.basename(file_path)
        file_location = os.path.join("files", file_name)
        with open(file_location, "wb") as f:
            f.write(file_data)
        self.users[recipient]["incoming"][str(uuid.uuid4())] = {
            "sender": sender,
            "file_path": file_location,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.users[sender]["outgoing"][str(uuid.uuid4())] = {
            "recipient": recipient,
            "file_path": file_location,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        return {"status": "OK"}

    def send_group_file(self, session_id, sender, recipients, file_path, encoded_file):
        file_data = base64.b64decode(encoded_file)
        file_name = os.path.basename(file_path)
        file_location = os.path.join("files", file_name)
        with open(file_location, "wb") as f:
            f.write(file_data)
        for recipient in recipients:
            if recipient not in self.users:
                return {"status": "ERROR", "message": "Recipient {} Not Found".format(recipient)}
            self.users[recipient]["incoming"][str(uuid.uuid4())] = {
                "sender": sender,
                "file_path": file_location,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        self.users[sender]["outgoing"][str(uuid.uuid4())] = {
            "recipients": recipients,
            "file_path": file_location,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        return {"status": "OK"}

    def add_realm(self, realm_id, realm_address, realm_port, data):
        if realm_id in self.realms:
            return {"status": "ERROR", "message": "Realm Already Exists"}
        self.realms[realm_id] = CommunicationThread({}, realm_address, realm_port)
        self.realms[realm_id].start()
        return {"status": "OK"}

    def receive_realm(self, realm_id, realm_address, realm_port, data):
        if realm_id in self.realms:
            return {"status": "ERROR", "message": "Realm Already Exists"}
        self.realms[realm_id] = CommunicationThread({}, realm_address, realm_port)
        self.realms[realm_id].start()
        return {"status": "OK"}

    def send_realm_message(self, session_id, realm_id, sender, recipient, message_content, data):
        if realm_id not in self.realms:
            return {"status": "ERROR", "message": "Realm Not Found"}
        message = {
            "msg_from": sender,
            "msg_to": recipient,
            "msg_content": message_content,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.realms[realm_id].add_message(message)
        return {"status": "OK"}

    def send_file_realm(self, session_id, realm_id, sender, recipient, file_path, encoded_file, data):
        if realm_id not in self.realms:
            return {"status": "ERROR", "message": "Realm Not Found"}
        file_data = base64.b64decode(encoded_file)
        file_name = os.path.basename(file_path)
        file_location = os.path.join("files", file_name)
        with open(file_location, "wb") as f:
            f.write(file_data)
        message = {
            "msg_from": sender,
            "msg_to": recipient,
            "file_path": file_location,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.realms[realm_id].add_message(message)
        return {"status": "OK"}

    def receive_file_realm(self, session_id, realm_id, sender, recipient, file_path, encoded_file, data):
        if realm_id not in self.realms:
            return {"status": "ERROR", "message": "Realm Not Found"}
        file_data = base64.b64decode(encoded_file)
        file_name = os.path.basename(file_path)
        file_location = os.path.join("files", file_name)
        with open(file_location, "wb") as f:
            f.write(file_data)
        message = {
            "msg_from": sender,
            "msg_to": recipient,
            "file_path": file_location,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.realms[realm_id].add_message(message)
        return {"status": "OK"}

    def receive_realm_message(self, realm_id, sender, recipient, message_content, data):
        if realm_id not in self.realms:
            return {"status": "ERROR", "message": "Realm Not Found"}
        message = {
            "msg_from": sender,
            "msg_to": recipient,
            "msg_content": message_content,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.realms[realm_id].add_message(message)
        return {"status": "OK"}

    def send_group_realm_message(self, session_id, realm_id, sender, recipients, message_content, data):
        if realm_id not in self.realms:
            return {"status": "ERROR", "message": "Realm Not Found"}
        for recipient in recipients:
            message = {
                "msg_from": sender,
                "msg_to": recipient,
                "msg_content": message_content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            self.realms[realm_id].add_message(message)
        return {"status": "OK"}

    def send_group_file_realm(self, session_id, realm_id, sender, recipients, file_path, encoded_file, data):
        if realm_id not in self.realms:
            return {"status": "ERROR", "message": "Realm Not Found"}
        file_data = base64.b64decode(encoded_file)
        file_name = os.path.basename(file_path)
        file_location = os.path.join("files", file_name)
        with open(file_location, "wb") as f:
            f.write(file_data)
        for recipient in recipients:
            message = {
                "msg_from": sender,
                "msg_to": recipient,
                "file_path": file_location,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            self.realms[realm_id].add_message(message)
        return {"status": "OK"}

    def receive_group_file_realm(self, session_id, realm_id, sender, recipients, file_path, encoded_file, data):
        if realm_id not in self.realms:
            return {"status": "ERROR", "message": "Realm Not Found"}
        file_data = base64.b64decode(encoded_file)
        file_name = os.path.basename(file_path)
        file_location = os.path.join("files", file_name)
        with open(file_location, "wb") as f:
            f.write(file_data)
        for recipient in recipients:
            message = {
                "msg_from": sender,
                "msg_to": recipient,
                "file_path": file_location,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            self.realms[realm_id].add_message(message)
        return {"status": "OK"}

    def receive_group_realm_message(self, realm_id, sender, recipients, message_content, data):
        if realm_id not in self.realms:
            return {"status": "ERROR", "message": "Realm Not Found"}
        for recipient in recipients:
            message = {
                "msg_from": sender,
                "msg_to": recipient,
                "msg_content": message_content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            self.realms[realm_id].add_message(message)
        return {"status": "OK"}

    def get_realm_inbox(self, username, realm_id):
        if realm_id not in self.realms:
            return {"status": "ERROR", "message": "Realm Not Found"}
        return {"status": "OK", "inbox": self.users[username]["incoming"]}

    def get_realm_chat(self, realm_id, username):
        if realm_id not in self.realms:
            return {"status": "ERROR", "message": "Realm Not Found"}
        return {"status": "OK", "chat": self.users[username]["outgoing"]}

    def logout(self):
        return {"status": "OK", "message": "Logout successful"}

    def info(self):
        return {"status": "OK", "message": "Chat Server Running"}

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    app = Chat()
    host = "0.0.0.0"
    port = 8889
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen(5)
        logging.warning(f"Server started on {host}:{port}")
        while True:
            client_socket, addr = server_socket.accept()
            with client_socket:
                logging.warning(f"Connection from {addr}")
                while True:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    response = app.process_request(data.decode())
                    client_socket.sendall(json.dumps(response).encode())
