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
        self.server_address = (TARGET_IP,TARGET_PORT)
        self.sock.connect(self.server_address)
        self.tokenid=""
    def proses(self,cmdline):
        j=cmdline.split(" ")
        try:
            command=j[0].strip()
            if (command=='auth'):
                username=j[1].strip()
                password=j[2].strip()
                return self.login(username,password)
            if (command=='register'):
                username=j[1].strip()
                password=j[2].strip()
                nama=j[3].strip()
                negara=j[4].strip()
                return self.register(username, password, nama, negara)
            elif (command=='addrealm'):
                realmid = j[1].strip()
                realm_address = j[2].strip()
                realm_port = j[3].strip()
                return self.add_realm(realmid, realm_address, realm_port)
            elif (command=='send'):
                usernameto = j[1].strip()
                message=""
                for w in j[2:]:
                    message="{} {}" . format(message,w)
                return self.send_message(usernameto,message)
            elif (command=='sendfile'):
                usernameto = j[1].strip()
                filepath = j[2].strip()
                return self.send_file(usernameto,filepath)
            elif (command=='sendgroup'):
                usernamesto = j[1].strip()
                message=""
                for w in j[2:]:
                    message="{} {}" . format(message,w)
                return self.send_group_message(usernamesto,message)
            elif (command=='sendgroupfile'):
                usernamesto = j[1].strip()
                filepath = j[2].strip()
                return self.send_group_file(usernamesto,filepath)
            elif (command == 'sendprivaterealm'):
                realmid = j[1].strip()
                username_to = j[2].strip()
                message = ""
                for w in j[3:]:
                    message = "{} {}".format(message, w)
                return self.send_realm_message(realmid, username_to, message)
            elif (command=='sendfilerealm'):
                realmid = j[1].strip()
                usernameto = j[2].strip()
                filepath = j[3].strip()
                return self.send_file_realm(realmid, usernameto,filepath)
            elif (command=='sendgrouprealm'):
                realmid = j[1].strip()
                usernamesto = j[2].strip()
                message=""
                for w in j[3:]:
                    message="{} {}" . format(message,w)
                return self.send_group_realm_message(realmid, usernamesto,message)
            elif (command=='sendgroupfilerealm'):
                realmid = j[1].strip()
                usernamesto = j[2].strip()
                filepath = j[3].strip()
                return self.send_group_file_realm(realmid, usernamesto,filepath)
            elif (command=='inbox'):
                return self.inbox()
            elif (command == 'getrealminbox'):
                realmid = j[1].strip()
                return self.realm_inbox(realmid)
            elif (command=='logout'):
                return self.logout()
            elif (command=='info'):
                return self.info()
            else:
                return "*Maaf, command tidak benar"
        except IndexError:
            return "-Maaf, command tidak benar"

    def sendstring(self,string):
        try:
            self.sock.sendall(string.encode())
            receivemsg = ""
            while True:
                data = self.sock.recv(1024)
                print("diterima dari server",data)
                if (data):
                    receivemsg = "{}{}" . format(receivemsg,data.decode())  #data harus didecode agar dapat di operasikan dalam bentuk string
                    if receivemsg[-4:]=='\r\n\r\n':
                        print("end of string")
                        return json.loads(receivemsg)
        except:
            self.sock.close()
            return { 'status' : 'ERROR', 'message' : 'Gagal'}

    def login(self,username,password):
        string="auth {} {} \r\n" . format(username,password)
        result = self.sendstring(string)
        if result['status']=='OK':
            self.tokenid=result['tokenid']
            return "username {} logged in, token {} " .format(username,self.tokenid)
        else:
            return "Error, {}" . format(result['message'])
    
    def register(self,username,password, nama, negara):
        string="register {} {} {} {}\r\n" . format(username,password, nama, negara)
        result = self.sendstring(string)
        if result['status']=='OK':
            self.tokenid=result['tokenid']
            return "username {} register in, token {} " .format(username,self.tokenid)
        else:
            return "Error, {}" . format(result['message'])

    def add_realm(self, realmid, realm_address, realm_port):
        if (self.tokenid==""):
            return "Error, not authorized"
        string="addrealm {} {} {} \r\n" . format(realmid, realm_address, realm_port)
        result = self.sendstring(string)
        if result['status']=='OK':
            return "Realm {} added" . format(realmid)
        else:
            return "Error, {}" . format(result['message'])

    def send_message(self,usernameto="xxx",message="xxx"):
        if (self.tokenid==""):
            return "Error, not authorized"
        string="send {} {} {} \r\n" . format(self.tokenid,usernameto,message)
        print(string)
        result = self.sendstring(string)
        if result['status']=='OK':
            return "message sent to {}" . format(usernameto)
        else:
            return "Error, {}" . format(result['message'])
        
    def send_file(self, usernameto="xxx", filepath="xxx"):
        if (self.tokenid==""):
            return "Error, not authorized"

        if not os.path.exists(filepath):
            return {'status': 'ERROR', 'message': 'File not found'}
        
        with open(filepath, 'rb') as file:
            file_content = file.read()
            encoded_content = base64.b64encode(file_content)  # Decode byte-string to UTF-8 string
        string="sendfile {} {} {} {}\r\n" . format(self.tokenid,usernameto,filepath,encoded_content)

        result = self.sendstring(string)
        if result['status']=='OK':
            return "file sent to {}" . format(usernameto)
        else:
            return "Error, {}" . format(result['message'])

    def send_realm_message(self, realmid, username_to, message):
        if (self.tokenid==""):
            return "Error, not authorized"
        string="sendprivaterealm {} {} {} {}\r\n" . format(self.tokenid, realmid, username_to, message)
        result = self.sendstring(string)
        if result['status']=='OK':
            return "Message sent to realm {}".format(realmid)
        else:
            return "Error, {}".format(result['message'])
        
    def send_file_realm(self, realmid, usernameto, filepath):
        if (self.tokenid==""):
            return "Error, not authorized"
        if not os.path.exists(filepath):
            return {'status': 'ERROR', 'message': 'File not found'}
        
        with open(filepath, 'rb') as file:
            file_content = file.read()
            encoded_content = base64.b64encode(file_content)  # Decode byte-string to UTF-8 string
        string="sendfilerealm {} {} {} {} {}\r\n" . format(self.tokenid, realmid, usernameto, filepath, encoded_content)
        result = self.sendstring(string)
        if result['status']=='OK':
            return "File sent to realm {}".format(realmid)
        else:
            return "Error, {}".format(result['message'])

    def send_group_message(self,usernames_to="xxx",message="xxx"):
        if (self.tokenid==""):
            return "Error, not authorized"
        string="sendgroup {} {} {} \r\n" . format(self.tokenid,usernames_to,message)
        print(string)
        result = self.sendstring(string)
        if result['status']=='OK':
            return "message sent to {}" . format(usernames_to)
        else:
            return "Error, {}" . format(result['message'])
        
    def send_group_file(self, usernames_to="xxx", filepath="xxx"):
        if (self.tokenid==""):
            return "Error, not authorized"
        
        if not os.path.exists(filepath):
            return {'status': 'ERROR', 'message': 'File not found'}
        
        with open(filepath, 'rb') as file:
            file_content = file.read()
            encoded_content = base64.b64encode(file_content)  # Decode byte-string to UTF-8 string

        string="sendgroupfile {} {} {} {}\r\n" . format(self.tokenid,usernames_to,filepath, encoded_content)

        result = self.sendstring(string)
        if result['status']=='OK':
            return "file sent to {}" . format(usernames_to)
        else:
            return "Error, {}" . format(result['message'])

    def send_group_realm_message(self, realmid, usernames_to, message):
        if self.tokenid=="":
            return "Error, not authorized"
        string="sendgrouprealm {} {} {} {} \r\n" . format(self.tokenid, realmid, usernames_to, message)

        result = self.sendstring(string)
        if result['status']=='OK':
            return "message sent to group {} in realm {}" .format(usernames_to, realmid)
        else:
            return "Error {}".format(result['message'])
        
    def send_group_file_realm(self, realmid, usernames_to, filepath):
        if self.tokenid=="":
            return "Error, not authorized"

        if not os.path.exists(filepath):
            return {'status': 'ERROR', 'message': 'File not found'}
        
        with open(filepath, 'rb') as file:
            file_content = file.read()
            encoded_content = base64.b64encode(file_content)  # Decode byte-string to UTF-8 string
        string="sendgroupfilerealm {} {} {} {} {}\r\n" . format(self.tokenid, realmid, usernames_to, filepath, encoded_content)

        result = self.sendstring(string)
        if result['status']=='OK':
            return "file sent to group {} in realm {}" .format(usernames_to, realmid)
        else:
            return "Error {}".format(result['message'])

    def inbox(self):
        if (self.tokenid==""):
            return "Error, not authorized"
        string="inbox {} \r\n" . format(self.tokenid)
        result = self.sendstring(string)
        if result['status']=='OK':
            return "{}" . format(json.dumps(result['messages']))
        else:
            return "Error, {}" . format(result['message'])

    def realm_inbox(self, realmid):
        if (self.tokenid==""):
            return "Error, not authorized"
        string="getrealminbox {} {} \r\n" . format(self.tokenid, realmid)
        print("Sending: " + string)
        result = self.sendstring(string)
        print("Received: " + str(result))
        if result['status']=='OK':
            return "Message received from realm {}: {}".format(realmid, result['messages'])
        else:
            return "Error, {}".format(result['message'])
    
    def logout(self):
        string="logout \r\n"
        result = self.sendstring(string)
        if result['status']=='OK':
            self.tokenid=""
            return "Logout Berhasil"
        else:
            return "Error, {}" . format(result['message'])

    def info(self):
        string="info {} \r\n"
        result = self.sendstring(string)
        list_user_aktif="User yang Aktif:\n"
        if result['status']=='OK':
            list_user_aktif += f"{result['message']}"
        return list_user_aktif

if __name__=="__main__":
    cc = ChatClient()
    c = Chat()
    while True:
        print("\n")
        print("List User: " + str(c.users.keys()) + " dan Passwordnya: " + str(c.users['messi']['password']) + ", " + str(c.users['henderson']['password']) + ", " + str(c.users['lineker']['password']))
        print("""Command:\n
        1. Login: auth [username] [password]\n
        2. Register: register [username] [password] [nama (gunakan "_" untuk seperator) ] [negara]\n
        3. Menambah realm: addrealm [nama_realm] [address] [port]\n
        4. Mengirim pesan: send [username to] [message]\n
        5. Mengirim file: senfile [username to] [filename]\n
        6. Mengirim pesan ke realm: sendrealm [name_realm] [username to] [message]\n
        7. Mengirim file ke realm: sendfilerealm [name_realm] [username to] [filename]\n
        8. Mengirim pesan ke group: sendgroup [usernames to] [message]\n
        9. Mengirim file ke group: sendgroupfile [usernames to] [filename]\n
        10. Mengirim pesan ke group realm: sendgrouprealm [name_realm] [usernames to] [message]\n
        11. Mengirim file ke group realm: sendgroupfilerealm [name_realm] [usernames to] [filename]\n
        12. Melihat pesan: inbox\n
        13. Melihat pesan realm: realminbox [nama_realm]\n
        14. Logout: logout\n
        15. Melihat user yang aktif: info\n""")
        cmdline = input("Command {}:" . format(cc.tokenid))
        print(cc.proses(cmdline))