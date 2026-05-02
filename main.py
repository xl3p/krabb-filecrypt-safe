# Стандартные библиотеки
import base64
import json
import secrets
import os
import types

# Сторонние библиотеки
import flet as ft
from argon2 import PasswordHasher
import cryptography
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


class SecureManager:
    def __init__(self, json_data, json_path):
        os.makedirs("encrypted", exist_ok=True)
        os.makedirs("salts", exist_ok=True)  # ← исправлено: создаём папку для солей
        self.jsdata = json_data
        self.json_path = json_path
        self.ph = PasswordHasher()

    def _save_and_hash_mkey(self, master_key):
        try:
            self.master_key_hash = self.ph.hash(master_key)
            self.jsdata["password"] = self.master_key_hash
            self.jsdata["password is registered"] = True
            self._save_json_data()
            return True
        except Exception:
            return False

    def _save_json_data(self):
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self.jsdata, f, indent=4)

    def generate_salt(self, size=16):
        return secrets.token_bytes(size)

    def load_salt(self, file_name):
        with open(f"salts/{file_name}.salt", "rb") as f:
            return f.read()

    def generate_key(self, file_name, password, salt=16, load_existing_salt=False, save_salt=True):
        if load_existing_salt:
            salt = self.load_salt(file_name)
        else:
            salt = self.generate_salt()

        if save_salt:
            with open(f"salts/{file_name}.salt", "wb") as file:
                file.write(salt)

        derived_key = self.derive_key(salt, password)
        return base64.urlsafe_b64encode(derived_key)

    def derive_key(self, salt, password):
        kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1)
        return kdf.derive(password.encode())

    def encrypt(self, file_path, file_name, key):
        with open(file_path, "rb") as f:
            file_data = f.read()

        fernet = Fernet(key)
        encrypted_file = fernet.encrypt(file_data)

        with open(f"encrypted/{file_name}", "wb") as f:
            f.write(encrypted_file)

    def decrypt(self, file_name, file_path, key):
        with open(f"encrypted/{file_name}", "rb") as f:
            encrypted_data = f.read()
        fernet = Fernet(key)
        try:
            decrypted_file = fernet.decrypt(encrypted_data)
            with open(file_path, "wb") as f:
                f.write(decrypted_file)
        except cryptography.fernet.InvalidToken:
            print("Invalid token")
            return


def main(page: ft.Page):
    page.title = "krabb secure vault"
    page.window.frameless = True
    page.window.width = 500
    page.window.height = 300
    page.encrypted_files = []
    page.selected_files = []

    page.update()

    # ---------------------------
    # Functions
    # ---------------------------

    def update_paths():
        with open("true_path.json", "w", encoding="utf-8") as file:
            json.dump(page.paths, file, indent=4)

    def encrypt_files(e):
        page.clean()
        page.add(main_page)
        status_output.value = ""
        verf_regmkey_field.value = ""
        page.update()

        total_files = len(e.files)

        try:
            for file in e.files:
                page.paths[file.name] = {
                    "true path": file.path
                }
                update_paths()

                key = page.secure_manager.generate_key(
                    file_name=file.name,
                    password=descrypted_key_field.value
                )
                page.secure_manager.encrypt(
                    file_name=file.name,
                    file_path=file.path,
                    key=key
                )
                progress.value = (file.id + 1) / total_files
                status_output.value = str(file.id + 1) + f" \\ {total_files}"
                page.update()

            status_output.value = "Files encrypted successfully!"
            status_output.color = "#6CFFA9"
            page.update()

        except Exception as ex:
            status_output.value = f"Error: {str(ex)}"
            status_output.color = "#FF4646"
            page.update()

    def update_directory_view():
        encrypted_filelist.controls.clear()

        if page.current_path != "encrypted":
            encrypted_filelist.controls.append(
                ft.ListTile(
                    title=ft.Text(".."),
                    leading=ft.Icon(ft.Icons.ARROW_BACK),
                    on_click=go_back,
                    data=os.path.dirname(page.current_path)
                )
            )

        for item in os.listdir(page.current_path):
            item_path = os.path.join(page.current_path, item)

            if os.path.isdir(item_path):
                encrypted_filelist.controls.append(
                    ft.ListTile(
                        title=ft.Text(item),
                        leading=ft.Icon(ft.Icons.FOLDER),
                        on_click=open_folder,
                        data=item_path,
                        icon_color="#A0CAFD"
                    )
                )
            else:
                encrypted_filelist.controls.append(
                    ft.ListTile(
                        title=ft.Text(item),
                        leading=ft.Icon(ft.Icons.INSERT_DRIVE_FILE),
                        on_click=select_file,
                        data=(item_path, item)
                    )
                )

        page.update()

    def open_folder(e):
        page.current_path = e.control.data
        update_directory_view()
        page.update()

    def go_back(e):
        page.current_path = e.control.data
        update_directory_view()
        page.update()

    def select_file(e):
        page.selected_files.append(e.control.data)
        page.update()

    def decrypt_files(e):
        if page.selected_files and file_filter_field.value:
            try:
                for i, (path, file_name) in enumerate(page.selected_files):
                    key = page.secure_manager.generate_key(
                        load_existing_salt=True,
                        save_salt=False,
                        file_name=file_name,
                        password=file_filter_field.value
                    )
                    page.secure_manager.decrypt(file_name, page.paths[file_name]["true path"], key)

                status_output.value = "Files decrypted successfully!"
                status_output.color = "#6CFFA9"

            except Exception as ex:
                status_output.value = f"Error: {str(ex)}"
                status_output.color = "#FF4646"
        else:
            status_output.value = "Please select files and enter password"
            status_output.color = "#FF4646"

        page.update()

    def change_screen(e):
        page.window.minimized = not page.window.minimized

    def change_page(e):
        if e.control.data:
            page.clean()
            page.add(pages.get(e.control.data[0]))
            page.window.width = e.control.data[1][0]
            page.window.height = e.control.data[1][1]
            page.update()

        if isinstance(e.control.data[2], types.FunctionType):
            e.control.data[2]()

    def update_all():
        status_output.clean()
        status_output.update()
        page.update()

    def ask_master_key(e):
        try:
            page.clean()
            page.add(verifity_mkey_page)
            page.window.height = 300
            verf_regmkey_field.clean()
            verf_regmkey_field.update()
            page.update()
            confirm_regmkey_btn.data = e.control.data
            update_all()

            if len(e.control.data) > 2:
                page.is_filepicker = True

            verf_regmkey_field.value = ""
            descrypted_key_field.value = ""
            status_output.value = ""
            verf_regmkey_field.update()
            status_output.update()

        except Exception as ex:
            print(f"Error in ask_master_key: {ex}")

    def initlization():
        try:
            with open("data.json", "r+", encoding="utf-8") as file:
                jsdata = json.load(file)
        except:
            jsdata = {
                "password is registered": False,
                "password": None
            }
            with open("data.json", "w", encoding="utf-8") as f:
                json.dump(jsdata, f, indent=4)

        try:
            with open("true_path.json", "r+", encoding="utf-8") as file:
                page.paths = json.load(file)
        except:
            page.paths = {}
            with open("true_path.json", "w", encoding="utf-8") as f:
                json.dump(page.paths, f, indent=4)

        page.secure_manager = SecureManager(json_data=jsdata, json_path="data.json")

        if "password is registered" in jsdata:
            if jsdata["password is registered"]:
                page.add(main_page)
                page.window.width = 500
                page.window.height = 250
                page.update()
            else:
                page.add(authorize_key_page)
                page.window.width = 500
                page.window.height = 300
                page.update()
        else:
            page.add(authorize_key_page)
            page.window.width = 500
            page.window.height = 300
            page.update()

    def confirm_master_key(e):
        page.secure_manager._save_and_hash_mkey(master_key_field.value)
        change_page(e)
        page.update()

    def verifity_masterkey(e):
        if master_key_field.value == confirm_mkey_field.value and len(master_key_field.value) > 4:
            status_output.value = "Correct!"
            status_output.color = "#6CFFA9"
            confirm_mkey_btn.disabled = False
            page.update()
        elif master_key_field.value == confirm_mkey_field.value and len(master_key_field.value) < 4:
            status_output.value = "The password must be longer than 4 characters long."
            status_output.color = "#FFE46E"
            confirm_mkey_btn.disabled = True
            page.update()
        else:
            status_output.value = "Passwords must match."
            status_output.color = "#FF4646"
            confirm_mkey_btn.disabled = True
            page.update()

    def verifity_registered_key(e):
        if len(e.control.value) > 4:
            mkey = e.control.value
            ph = PasswordHasher()
            with open("data.json", "r", encoding="utf-8") as f:
                jsdata = json.load(f)
            try:
                if ph.verify(jsdata["password"], mkey):
                    status_output.value = "Correct"
                    status_output.color = "#6CFFA9"
                    confirm_regmkey_btn.disabled = False
                    page.update()
                else:
                    status_output.value = "Incorrect key"
                    status_output.color = "#FF4646"
                    confirm_regmkey_btn.disabled = True
                    page.update()
            except:
                status_output.value = "Incorrect key"
                status_output.color = "#FF4646"
                confirm_regmkey_btn.disabled = True
                page.update()
        else:
            status_output.value = "Incorrect key"
            status_output.color = "#FF4646"
            confirm_regmkey_btn.disabled = True
            page.update()

    def verifity_password(e, button: ft.Button, target: int):
        if len(e.control.value) >= target:
            status_output.value = "Correct!"
            status_output.color = "#6CFFA9"
            button.disabled = False
            page.update()
        else:
            status_output.value = f"The password length must be greater than or equal to {target} characters."
            status_output.color = "#FFE46E"
            button.disabled = True
            page.update()

    # ---------------------------
    # Variables
    # ---------------------------

    page.is_filepicker = None
    page.current_path = "encrypted"

    master_key_field = ft.TextField(
        label="Password",
        password=True,
        can_reveal_password=True,
        width=350, multiline=False,
        on_change=verifity_masterkey
    )

    confirm_mkey_field = ft.TextField(
        label="Confirm password",
        password=True,
        can_reveal_password=True,
        width=350, multiline=False,
        on_change=verifity_masterkey
    )

    status_output = ft.Text("   ", width=250)

    confirm_mkey_btn = ft.ElevatedButton(
        "Confirm",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        data=("Main", (500, 250)),
        on_click=confirm_master_key,
        disabled=True
    )

    progress = ft.ProgressBar(width=375)

    confirm_regmkey_btn = ft.ElevatedButton(
        "Confirm",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        on_click=change_page,
        disabled=True
    )

    verf_regmkey_field = ft.TextField(
        password=True, autofocus=True,
        can_reveal_password=True,
        on_change=verifity_registered_key
    )

    confirm_decripted_key_btn = ft.ElevatedButton(
        "Confirm",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        data=("Main", (500, 250)),
        on_click=lambda e: file_picker.pick_files(allow_multiple=True),
        disabled=True
    )

    descrypted_key_field = ft.TextField(
        password=True, autofocus=True,
        can_reveal_password=True,
        on_change=lambda e: verifity_password(e, confirm_decripted_key_btn, 4)
    )

    file_picker = ft.FilePicker(on_result=encrypt_files)
    page.overlay.append(file_picker)

    decrypt_filepicker = ft.FilePicker()
    page.overlay.append(decrypt_filepicker)

    encrypted_filelist = ft.ListView(height=360, expand=True)

    file_filter_field = ft.TextField(
        password=True, can_reveal_password=True,
        label="Password Filter", width=300
    )

    # ---------------------------
    # Pages
    # ---------------------------

    page.appbar = ft.AppBar(
        leading=ft.Container(
            ft.WindowDragArea(ft.Icon(ft.Icons.SECURITY), expand=True),
            width=100
        ),
        title=ft.Container(
            ft.WindowDragArea(ft.Text("krabb secure vault", size=13), expand=True),
            width=800
        ),
        bgcolor="#15111B",
        toolbar_height=30,
        actions=[
            ft.Container(
                ft.WindowDragArea(
                    ft.Row([
                        ft.IconButton(icon=ft.Icons.MINIMIZE, icon_size=13, on_click=change_screen),
                        ft.IconButton(icon=ft.Icons.CLOSE, icon_size=13, on_click=lambda e: page.window.close())
                    ], expand=True),
                    expand=True
                ),
                expand=True
            )
        ]
    )

    ask_decrypt_key_page = ft.Column([
        ft.Row([ft.IconButton(icon=ft.Icons.CANCEL, icon_size=24, on_click=change_page, data=("Main", (500, 250)))]),
        ft.Text("Create an unlock key for the file(s)", size=25),
        descrypted_key_field,
        ft.Container(ft.Divider(color="#B1C2C7"), padding=5, height=20, expand=True),
        ft.Row([confirm_decripted_key_btn, status_output])
    ])

    verifity_mkey_page = ft.Column([
        ft.Row([ft.IconButton(icon=ft.Icons.CANCEL, icon_size=24, on_click=change_page, data=("Main", (500, 250)))]),
        ft.Text("Enter the registered key", size=25),
        verf_regmkey_field,
        ft.Container(ft.Divider(color="#B1C2C7"), padding=5, height=20, expand=True),
        ft.Row([confirm_regmkey_btn, status_output])
    ])

    decrypt_menu = ft.Column([
        ft.Row([ft.IconButton(icon=ft.Icons.CANCEL, icon_size=24, on_click=change_page, data=("Main", (500, 250)))]),
        ft.Container(ft.Divider(color="#B1C2C7"), padding=5, height=20, expand=True),
        encrypted_filelist,
        ft.Container(ft.Divider(color="#B1C2C7"), padding=5, height=20, expand=True),
        ft.Row([
            file_filter_field,
            ft.ElevatedButton(
                text="Okey",
                icon=ft.Icons.FILTER,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
            )
        ]),
        ft.Row([
            status_output,
            ft.Text("      ", size=30),
            ft.ElevatedButton(
                "Decrypt",
                icon=ft.Icons.LOCK_OPEN,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                on_click=decrypt_files
            )
        ], expand=True)
    ])

    main_page = ft.Column([
        ft.Text(" ", size=15),
        ft.ElevatedButton(
            text="Encrypt",
            icon=ft.Icons.LOCK,
            on_click=ask_master_key,
            data=("Ask decripted key", (500, 300), "FilePicker"),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            width=100,
            height=33
        ),
        ft.Text(" ", size=1),
        ft.ElevatedButton(
            text="Decrypt",
            icon=ft.Icons.LOCK_OPEN,
            on_click=ask_master_key,
            data=("Decrypt menu", (430, 630), update_directory_view),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        ),
        ft.Container(ft.Divider(color="#B1C2C7"), padding=5, height=20, expand=True),
        ft.Container(ft.Column([progress, status_output]), padding=10)
    ])

    authorize_key_page = ft.Column([
        ft.Text("Welcome to secure!", size=25),
        master_key_field,
        confirm_mkey_field,
        ft.Container(ft.Divider(color="#B1C2C7"), padding=10),
        ft.Row([confirm_mkey_btn, status_output])
    ])

    pages = {
        "Main": main_page,
        "Decrypt menu": decrypt_menu,
        "Ask decripted key": ask_decrypt_key_page
    }

    initlization()


if __name__ == "__main__":
    ft.app(target=main, name="krabb secure vault", view=ft.AppView.FLET_APP_WEB)