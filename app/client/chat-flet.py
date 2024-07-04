import flet as ft
import json
from chatcli import ChatClient
import os

TARGET_IP = os.getenv("SERVER_IP") or "127.0.0.1"
TARGET_PORT = os.getenv("SERVER_PORT") or "8889"
ON_WEB = os.getenv("ONWEB") or "1"


class ChatList(ft.Container):
    def __init__(self, page, users, from_user):
        super().__init__()
        for value in users.values():
            print(value["username"])
        self.content = ft.Column(
            [
                ft.ListTile(
                    leading=ft.Icon(ft.icons.PERSON),
                    title=ft.Text(f"{value['username']}"),
                    on_click=lambda _: page.go(f"/private/{value['username']}"),
                )
                for value in users.values()
            ],
        )

        self.padding = ft.padding.symmetric(vertical=10)
        
class GroupChatList(ft.Container):
    def __init__(self, page, groups):
        super().__init__()
        # Log the group names for debugging purposes
        for value in groups.values():
            print(value["group_name"])

        # Creating the UI for the list of groups
        self.content = ft.Column(
            [
                ft.ListTile(
                    leading=ft.Icon(ft.icons.GROUP),
                    title=ft.Text(f"{value['group_name']}"),
                    on_click=lambda _: page.go(f"/group/{value['group_id']}"),
                )
                for value in groups.values()
            ],
        )
        self.padding = ft.padding.symmetric(vertical=10)



class ChatRoom:
    def __init__(self, page, cc, from_user, to_user):
        self.chat = ft.TextField(
            label="Write a message...",
            autofocus=True,
            expand=True,
            on_submit=self.send_click,
        )
        self.lv = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=True)
        self.send = ft.IconButton(
            icon=ft.icons.SEND_ROUNDED,
            tooltip="Send message",
            on_click=self.send_click,
        )
        self.file_picker = ft.FilePicker(on_result=self.upload_files, on_upload=self.upload_server)
        self.file_pick = ft.IconButton(
            icon=ft.icons.UPLOAD_FILE_ROUNDED,
            tooltip="Send file",
            on_click=self.on_pick_file,
        )
        self.page = page
        self.cc = cc
        self.from_user = from_user
        self.to_user = to_user
        self.page.pubsub.subscribe(self.on_chat)

    def on_pick_file(self, __e__):
        self.page.overlay.append(self.file_picker)
        self.page.update()
        self.file_picker.pick_files(allow_multiple=True)

    def send_click(self, __e__):
        if not self.chat.value:
            self.chat.error_text = "Please enter message"
            self.page.update()
        else:
            command = f"send {self.to_user} {self.chat.value}"
            server_call = self.cc.proses(command)
            self.lv.controls.append(ft.Text("To {}: {}".format(self.to_user, self.chat.value)))

            if "sent" in server_call:
                self.page.pubsub.send_all(self.chat.value)

            self.chat.value = ""
            self.chat.focus()
            self.page.update()

    def on_chat(self, message):
        check_inbox = json.loads(self.cc.inbox())
        self.lv.controls.append(ft.Text("From {}: {}".format(check_inbox[self.to_user][0]['msg_from'], check_inbox[self.to_user][0]['msg'])))
        self.page.update()

    def upload_files(self, e: ft.FilePickerResultEvent):
        upload_list = []
        if self.file_picker.result is not None and self.file_picker.result.files is not None:
            for f in self.file_picker.result.files:
                upload_list.append(
                    ft.FilePickerUploadFile(
                        f.name,
                        upload_url=self.page.get_upload_url(f.name, 600),
                    )
                )
            self.file_picker.upload(upload_list)

    def upload_server(self, e: ft.FilePickerUploadEvent):
        if e.progress == 1:
            command = f"sendfile {self.to_user} app\\client\\upload\\{e.file_name}"
            server_call = self.cc.proses(command)
            self.lv.controls.append(ft.Text("To {}: Berhasil mengirim file {}".format(self.to_user, e.file_name)))

            if "sent" in server_call:
                self.page.pubsub.send_all(self.chat.value)

            self.chat.value = ""
            self.chat.focus()
            self.page.update()
            
class GroupChatRoom:
    def __init__(self, page, cc, group_id):
        self.chat = ft.TextField(
            label="Write a message...",
            autofocus=True,
            expand=True,
            on_submit=self.send_click,
        )
        self.lv = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=True)
        self.send = ft.IconButton(
            icon=ft.icons.SEND_ROUNDED,
            tooltip="Send message",
            on_click=self.send_click,
        )
        self.file_picker = ft.FilePicker(on_result=self.upload_files, on_upload=self.upload_server)
        self.file_pick = ft.IconButton(
            icon=ft.icons.UPLOAD_FILE_ROUNDED,
            tooltip="Send file",
            on_click=self.on_pick_file,
        )
        self.page = page
        self.cc = cc
        self.group_id = group_id
        self.page.pubsub.subscribe(self.on_chat)

    def on_pick_file(self, __e__):
        self.page.overlay.append(self.file_picker)
        self.page.update()
        self.file_picker.pick_files(allow_multiple=True)

    def send_click(self, __e__):
        if not self.chat.value:
            self.chat.error_text = "Please enter message"
            self.page.update()
        else:
            command = f"sendgroup {self.group_id} {self.chat.value}"
            server_call = self.cc.proses(command)
            self.lv.controls.append(ft.Text("To group {}: {}".format(self.group_id, self.chat.value)))

            if "sent" in server_call:
                self.page.pubsub.send_all(self.chat.value)

            self.chat.value = ""
            self.chat.focus()
            self.page.update()

    def on_chat(self, message):
        check_inbox = json.loads(self.cc.inbox_group())
        self.lv.controls.append(ft.Text("From {}: {}".format(check_inbox[self.group_id][0]['msg_from'], check_inbox[self.group_id][0]['msg'])))
        self.page.update()

    def upload_files(self, e: ft.FilePickerResultEvent):
        upload_list = []
        if self.file_picker.result is not None and self.file_picker.result.files is not None:
            for f in self.file_picker.result.files:
                upload_list.append(
                    ft.FilePickerUploadFile(
                        f.name,
                        upload_url=self.page.get_upload_url(f.name, 600),
                    )
                )
            self.file_picker.upload(upload_list)

    def upload_server(self, e: ft.FilePickerUploadEvent):
        if e.progress == 1:
            command = f"sendfilegroup {self.group_id} app\\client\\upload\\{e.file_name}"
            server_call = self.cc.proses(command)
            self.lv.controls.append(ft.Text("To group {}: Berhasil mengirim file {}".format(self.group_id, e.file_name)))

            if "sent" in server_call:
                self.page.pubsub.send_all(self.chat.value)

            self.chat.value = ""
            self.chat.focus()
            self.page.update()



def main(page):
    cc = ChatClient()
    page.title = "Chat App"
    is_login = False

    global login_dialog
    def login_dialog():
        nonlocal is_login
        global changeto_login
        global logouttologin
        global changeto_logout

        def changeto_register(e):
            page.dialog.title=ft.Text(
                "Welcome! Please Fill Bellow to register", style=ft.TextThemeStyle.TITLE_MEDIUM
            )
            page.dialog.actions=[
                ft.ElevatedButton("Already have an account", on_click=changeto_login),
                ft.ElevatedButton("Register", on_click=register_click)
            ]
            page.dialog.content=ft.Column([username, password,name,country], tight=True)
            page.update()
        
        def changeto_login(e):
            page.dialog.title=ft.Text(
                "Welcome! Please login", style=ft.TextThemeStyle.TITLE_MEDIUM
            )
            page.dialog.actions=[
                ft.ElevatedButton("Register Account", on_click=changeto_register),
                ft.ElevatedButton("Login", on_click=login_click)
            ]
            page.dialog.content=ft.Column([username, password], tight=True)

            page.update()


        page.dialog = ft.AlertDialog(
            open=not is_login,
            modal=True,
            title=ft.Text(
                "Welcome! Please login", style=ft.TextThemeStyle.TITLE_MEDIUM
            ),
            content=ft.Column([username, password], tight=True),
            actions=[
                ft.ElevatedButton("Register Account", on_click=changeto_register),
                ft.ElevatedButton("Login", on_click=login_click)
            ],
            actions_alignment="end",
        )

    def register_click(__e__):
        if not username.value:
            username.error_text = "Please enter username"
            username.update()
        else :
            username.error_text = ""
            username.update()


        if not password.value:
            password.error_text = "Please enter password"
            password.update()
        else :
            password.error_text = ""
            password.update()
        
        if not name.value:
            name.error_text = "Please enter name"
            name.update()
        else :
            name.error_text = ""
            name.update()

        if not country.value:
            country.error_text = "Please enter country"
            country.update()
        else :
            country.error_text = ""
            country.update()

        if username.value != "" and password.value != "" and name.value != "" and country.value != "":
            login = cc.register(username.value, password.value, name.value, country.value)

            if "Error" in login:
                country.error_text = "Error When Register"
                country.update()

            else:
                username.value = ""
                password.value = ""
                name.value = ""
                country.value = ""
                username.error_text = ""
                password.error_text = ""
                name.error_text = ""
                country.error_text = ""
                page.update()
                changeto_login(None)
            page.update()

    def login_click(__e__):
        if not username.value:
            username.error_text = "Please enter username"
            username.update()
        else :
            username.error_text = ""
            username.update()


        if not password.value:
            password.error_text = "Please enter password"
            password.update()
        else :
            password.error_text = ""
            password.update()

        if username.value != "" and password.value != "":
            login = cc.login(username.value, password.value)

            if "Error" in login:
                username.error_text = "Username or Password does not match"
                password.error_text = "Username or Password does not match"
                username.update()

            else:
                menu_item_username.text = "welcome, " + username.value
                username.value = ""
                password.value = ""
                username.error_text = ""
                password.error_text = ""
                is_login = True
                page.dialog.open = False

            page.update()
    
    def logout_click(e):
        is_login = False
        cc.logout()
        login_dialog()
        page.update()

    username = ft.TextField(label="Username", autofocus=True)
    password = ft.TextField(
        label="Password",
        password=True,
        can_reveal_password=True,
        autofocus=True,
        on_submit=login_click,
    )
    name = ft.TextField(label="name", autofocus=True)
    country = ft.TextField(label="country", autofocus=True)
    
    login_dialog()

    global menu_item_username
    menu_item_username = ft.PopupMenuItem(text="")
    menu = ft.PopupMenuButton(
        items=[
            menu_item_username,
            ft.PopupMenuItem(
                icon=ft.icons.LOGOUT, text="Logout", on_click=logout_click
            ),
        ]
    )

    def route_change(__route__):
        troute = ft.TemplateRoute(page.route)
        page.views.clear()

        page.views.append(
            ft.View(
                "/",
                [
                    menu,
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.ListTile(
                                        leading=ft.Icon(ft.icons.PERSON),
                                        title=ft.Text("Private Chat"),
                                        on_click=lambda _: page.go("/private"),
                                    ),
                                    ft.ListTile(
                                        leading=ft.Icon(ft.icons.GROUP),
                                        title=ft.Text("Group Chat"),
                                        on_click=lambda _: page.go("/group"),
                                    ),
                                ],
                            ),
                            padding=ft.padding.symmetric(vertical=10),
                        )
                    ),
                ],
            )
        )

        if troute.match("/private"):
            page.views.append(
                ft.View(
                    "/private",
                    [
                        ft.AppBar(title=ft.Text("Private Chat"), actions=[menu]),
                        ft.Card(
                            content=ChatList(page, cc.info(), cc.username),
                        ),
                    ],
                )
            )

        elif troute.match("/private/:username"):
            cr = ChatRoom(page, cc, cc.username, troute.username)
            
            page.views.append(
                ft.View(
                    f"/private/{troute.username}",
                    [
                        ft.AppBar(
                            title=ft.Text(f"Private Chat with {troute.username}"),
                            actions=[menu],
                        ),
                        cr.lv,
                        ft.Row([cr.chat, cr.send, cr.file_pick]),
                    ],
                )
            )

        elif troute.match("/group"):
            page.views.append(
                ft.View(
                    "/group",
                    [
                        ft.AppBar(title=ft.Text("Group Chat"), actions=[menu]),
                        GroupChatList(page, cc.groups()),  # Menampilkan daftar grup
                    ],
                )
            )

        elif troute.match("/group/:group_id"):
            gc = GroupChatRoom(page, cc, troute.group_id)
            
            page.views.append(
                ft.View(
                    f"/group/{troute.group_id}",
                    [
                        ft.AppBar(
                            title=ft.Text(f"Group Chat: {troute.group_id}"),
                            actions=[menu],
                        ),
                        gc.lv,
                        ft.Row([gc.chat, gc.send, gc.file_pick]),
                    ],
                )
            )
        page.update()



    def view_pop(__view__):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)


if __name__ == "__main__":
    if ON_WEB == "1":
        ft.app(target=main, view=ft.WEB_BROWSER, port=8550, upload_dir="upload")
    else:
        ft.app(target=main)
