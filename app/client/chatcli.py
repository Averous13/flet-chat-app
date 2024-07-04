import socket
import json
import base64
import json
import os
from chat import Chat

TARGET_IP = "127.0.0.1"
TARGET_PORT = 8889


class ChatClient:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (TARGET_IP, TARGET_PORT)
        self.sock.connect(self.server_address)
        self.tokenid = ""
        self.username = ""

    def proses(self, cmdline):
        j = cmdline.split(" ")
        try:
            command = j[0].strip()
            if command == "auth":
                username = j[1].strip()
                password = j[2].strip()
                return self.login(username, password)
            if command == "register":
                username = j[1].strip()
                password = j[2].strip()
                nama = j[3].strip()
                negara = j[4].strip()
                return self.register(username, password, nama, negara)
            elif command == "addrealm":
                realmid = j[1].strip()
                realm_address = j[2].strip()
                realm_port = j[3].strip()
                return self.add_realm(realmid, realm_address, realm_port)
            elif command == "send":
                usernameto = j[1].strip()
                message = ""
                for w in j[2:]:
                    message = "{} {}".format(message, w)
                return self.send_message(usernameto, message)
            elif command == "sendfile":
                usernameto = j[1].strip()
                filepath = j[2].strip()
                return self.send_file(usernameto, filepath)
            elif command == "sendgroup":
                usernamesto = j[1].strip()
                message = ""
                for w in j[2:]:
                    message = "{} {}".format(message, w)
                return self.send_group_message(usernamesto, message)
            elif command == "sendgroupfile":
                usernamesto = j[1].strip()
                filepath = j[2].strip()
                return self.send_group_file(usernamesto, filepath)
            elif command == "sendrealm":
                realmid = j[1].strip()
                usernameto = j[2].strip()
                message = ""
                for w in j[3:]:
                    message = "{} {}".format(message, w)
                return self.send_realm_message(realmid, usernameto, message)
            elif command == "sendfilerealm":
                realmid = j[1].strip()
                usernameto = j[2].strip()
                filepath = j[3].strip()
                return self.send_file_realm(realmid, usernameto, filepath)
            elif command == "sendgrouprealm":
                realmid = j[1].strip()
                usernamesto = j[2].strip()
                message = ""
                for w in j[3:]:
                    message = "{} {}".format(message, w)
                return self.send_group_realm_message(realmid, usernamesto, message)
            elif command == "sendgroupfilerealm":
                realmid = j[1].strip()
                usernamesto = j[2].strip()
                filepath = j[3].strip()
                return self.send_group_file_realm(realmid, usernamesto, filepath)
            elif command == "inbox":
                return self.get_inbox()
            elif command == "realminbox":
                realmid = j[1].strip()
                return self.get_realm_inbox(realmid)
            elif command == "logout":
                return self.logout()
            elif command == "info":
                return self.info()
            else:
                return "Command tidak dikenali"
        except IndexError:
            return "Command tidak lengkap"

    def sendstring(self, string):
        try:
            self.sock.sendall(string.encode())
            receivedmsg = ""
            while True:
                data = self.sock.recv(1024)
                if data:
                    receivedmsg = "{}{}".format(receivedmsg, data.decode())
                    if receivedmsg[-4:] == "\r\n\r\n":
                        return json.loads(receivedmsg)
        except:
            self.sock.close()
            return {"status": "ERROR", "message": "Gagal"}

    def login(self, username, password):
        string = "auth {} {} \r\n".format(username, password)
        result = self.sendstring(string)
        if result["status"] == "OK":
            self.tokenid = result["tokenid"]
            return "Login Berhasil"
        else:
            return "Error, {}".format(result["message"])

    def register(self, username, password, nama, negara):
        string = "register {} {} {} {} \r\n".format(username, password, nama, negara)
        result = self.sendstring(string)
        if result["status"] == "OK":
            self.tokenid = result["tokenid"]
            return "Register Berhasil"
        else:
            return "Error, {}".format(result["message"])

    def add_realm(self, realmid, realm_address, realm_port):
        string = "addrealm {} {} {} \r\n".format(realmid, realm_address, realm_port)
        result = self.sendstring(string)
        if result["status"] == "OK":
            return "Add Realm Berhasil"
        else:
            return "Error, {}".format(result["message"])

    def send_message(self, usernameto, message):
        string = "send {} {} {}\r\n".format(self.tokenid, usernameto, message)
        result = self.sendstring(string)
        if result["status"] == "OK":
            return "Pesan berhasil dikirim"
        else:
            return "Error, {}".format(result["message"])

    def send_file(self, usernameto, filepath):
        if os.path.exists(filepath):
            with open(filepath, "rb") as file:
                encoded_file = base64.b64encode(file.read()).decode()
            string = "sendfile {} {} {} {}\r\n".format(
                self.tokenid, usernameto, filepath, encoded_file
            )
            result = self.sendstring(string)
            if result["status"] == "OK":
                return "File berhasil dikirim"
            else:
                return "Error, {}".format(result["message"])
        else:
            return "Error, file tidak ditemukan"

    def send_group_message(self, usernamesto, message):
        string = "sendgroup {} {} {}\r\n".format(self.tokenid, usernamesto, message)
        result = self.sendstring(string)
        if result["status"] == "OK":
            return "Pesan grup berhasil dikirim"
        else:
            return "Error, {}".format(result["message"])

    def send_group_file(self, usernamesto, filepath):
        if os.path.exists(filepath):
            with open(filepath, "rb") as file:
                encoded_file = base64.b64encode(file.read()).decode()
            string = "sendgroupfile {} {} {} {}\r\n".format(
                self.tokenid, usernamesto, filepath, encoded_file
            )
            result = self.sendstring(string)
            if result["status"] == "OK":
                return "File grup berhasil dikirim"
            else:
                return "Error, {}".format(result["message"])
        else:
            return "Error, file tidak ditemukan"

    def send_realm_message(self, realmid, usernameto, message):
        string = "sendprivaterealm {} {} {} {}\r\n".format(
            self.tokenid, realmid, usernameto, message
        )
        result = self.sendstring(string)
        if result["status"] == "OK":
            return "Pesan realm berhasil dikirim"
        else:
            return "Error, {}".format(result["message"])

    def send_file_realm(self, realmid, usernameto, filepath):
        if os.path.exists(filepath):
            with open(filepath, "rb") as file:
                encoded_file = base64.b64encode(file.read()).decode()
            string = "sendfilerealm {} {} {} {} {}\r\n".format(
                self.tokenid, realmid, usernameto, filepath, encoded_file
            )
            result = self.sendstring(string)
            if result["status"] == "OK":
                return "File realm berhasil dikirim"
            else:
                return "Error, {}".format(result["message"])
        else:
            return "Error, file tidak ditemukan"

    def send_group_realm_message(self, realmid, usernamesto, message):
        string = "sendgrouprealm {} {} {} {}\r\n".format(
            self.tokenid, realmid, usernamesto, message
        )
        result = self.sendstring(string)
        if result["status"] == "OK":
            return "Pesan grup realm berhasil dikirim"
        else:
            return "Error, {}".format(result["message"])

    def send_group_file_realm(self, realmid, usernamesto, filepath):
        if os.path.exists(filepath):
            with open(filepath, "rb") as file:
                encoded_file = base64.b64encode(file.read()).decode()
            string = "sendgroupfilerealm {} {} {} {} {}\r\n".format(
                self.tokenid, realmid, usernamesto, filepath, encoded_file
            )
            result = self.sendstring(string)
            if result["status"] == "OK":
                return "File grup realm berhasil dikirim"
            else:
                return "Error, {}".format(result["message"])
        else:
            return "Error, file tidak ditemukan"

    def get_inbox(self):
        string = "inbox {} \r\n".format(self.tokenid)
        result = self.sendstring(string)
        if result["status"] == "OK":
            return "{}".format(json.dumps(result["messages"]))
        else:
            return "Error, {}".format(result["message"])

    def get_realm_inbox(self, realmid):
        string = "realminbox {} {} \r\n".format(self.tokenid, realmid)
        result = self.sendstring(string)
        if result["status"] == "OK":
            return "{}".format(json.dumps(result["messages"]))
        else:
            return "Error, {}".format(result["message"])

    def logout(self):
        string = "logout {} \r\n".format(self.tokenid)
        result = self.sendstring(string)
        if result["status"] == "OK":
            self.tokenid = ""
            return "Logout Berhasil"
        else:
            return "Error, {}".format(result["message"])

    def info(self):
        string = "info {} \r\n"
        result = self.sendstring(string)
        if result["status"] == "OK":
            return result["message"]


if __name__ == "__main__":
    cc = ChatClient()
    c = Chat()
    while True:
        print("\n")
        print(
            "List User: "
            + str(c.users.keys())
            + " dan Passwordnya: "
            + str(c.users["messi"]["password"])
            + ", "
            + str(c.users["henderson"]["password"])
            + ", "
            + str(c.users["lineker"]["password"])
        )
        print(
            """Command:\n
        1. Login: auth [username] [password]\n
        2. Register: register [username] [password] [nama (gunakan "_" untuk seperator) ] [negara]\n
        3. Menambah realm: addrealm [nama_realm] [address] [port]\n
        4. Mengirim pesan: send [username to] [message]\n
        5. Mengirim file: sendfile [username to] [filename]\n
        6. Mengirim pesan ke realm: sendrealm [name_realm] [username to] [message]\n
        7. Mengirim file ke realm: sendfilerealm [name_realm] [username to] [filename]\n
        8. Mengirim pesan ke group: sendgroup [usernames to] [message]\n
        9. Mengirim file ke group: sendgroupfile [usernames to] [filename]\n
        10. Mengirim pesan ke group realm: sendgrouprealm [name_realm] [usernames to] [message]\n
        11. Mengirim file ke group realm: sendgroupfilerealm [name_realm] [usernames to] [filename]\n
        12. Melihat pesan: inbox\n
        13. Melihat pesan realm: realminbox [nama_realm]\n
        14. Logout: logout\n
        15. Melihat user yang aktif: info\n"""
        )
        cmdline = input("Command {}:".format(cc.tokenid))
        print(cc.proses(cmdline))
