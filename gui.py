from PyQt5.QtWidgets import QApplication, QWidget, QListWidgetItem, QListWidget, QVBoxLayout, QLineEdit, QComboBox, QPushButton, QLabel, QMessageBox, QStackedWidget
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
import script
import json
import os

"""
Parameters
"""

house_json_file_name = 'fetch_data.json'

"""
Utils
"""
def is_valid_email(email):
    # regrex
    import re
    email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_pattern, email):
        return "WrongEmail"
    
    # check if Microsoft(Outlook/Hotmail) or Gmail
    if "gmail.com" in email:
        return "Google"
    elif "outlook.com" in email or "hotmail.com" in email:
        return "Microsoft"
    else:
        return "WrongType"

"""
SCHEDULE
"""
class ScheduleObserver(QThread):
    signal = pyqtSignal(str)

    def __init__(self, sender_email, receiver_email, password, selected_cities, sender_email_type, timer, url, tg_api_token, tg_chat_id, does_send_to_tg):
        super().__init__()
        self.sender_email = sender_email
        self.tg_api_token = tg_api_token
        self.tg_chat_id = tg_chat_id
        self.receiver_email = receiver_email
        self.password = password
        self.selected_cities = selected_cities
        self.sender_email_type = sender_email_type
        self.timer = timer
        self.url = url
        self.does_send_to_telegram = does_send_to_tg

    def run(self):
        import schedule
        import time
        self.observe()
        time.sleep(1)
        schedule.every(int(self.timer)).seconds.do(self.observe)
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    def observe(self):
        # call main
        if self.url != "":
            # print("Empty URL")
            script.main(self.sender_email, self.receiver_email, self.password, self.selected_cities, self.sender_email_type, self.tg_api_token, self.tg_chat_id, self.does_send_to_telegram, self.url)
        else:
            script.main(self.sender_email, self.receiver_email, self.password, self.selected_cities, self.sender_email_type, self.tg_api_token, self.tg_chat_id, self.does_send_to_telegram)
    
"""
GUI SETUP
"""
class App(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    @pyqtSlot()
    def click_observe_button(self):
        """
        (1) Data check
        """
        self.sender_email = self.sender_email_input.text()
        self.receiver_email = self.receiver_email_input.text()
        self.password = self.password_input.text()
        self.timer = self.timer_input.text()
        self.url = self.url_input.text()
        self.tg_api_token = self.tg_api_token_input.text()
        self.tg_chat_id = self.tg_chat_id_input.text()
        self.does_send_to_telegram = False
        msg = QMessageBox()
        if self.tg_api_token != "" and self.tg_chat_id != "": self.does_send_to_telegram = True
        print(self.does_send_to_telegram)
        # Empty inputs for email
        if not self.does_send_to_telegram and (self.sender_email == "" or self.receiver_email == "" or self.password == "" or self.timer == ""):
            msg.setIcon(QMessageBox.Warning)
            msg.setText("You left input(s) blank. Please try again ...")
            msg.setWindowTitle("Inputs Empty Error")
            msg.exec_()
            return
        # Email Format for both S/R
        if not self.does_send_to_telegram and (is_valid_email(self.sender_email) == "WrongEmail" or is_valid_email(self.receiver_email) == "WrongEmail"):
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Invalid sender or reciver email(s) format. Please check again ...")
            msg.setWindowTitle("Email Format Error")
            msg.exec_()
            return
        # Email Type for Sender side
        if not self.does_send_to_telegram and (is_valid_email(self.sender_email) == "WrongType"):
            msg.setIcon(QMessageBox.Warning)
            msg.setText("For now, only Gmail or Microsoft for sender email. Please change your type of email ...")
            msg.setWindowTitle("Email Type Error")
            msg.exec_()
            return
        # Timers range : 1-3600 seconds
        if not self.timer.isdigit(): # not digit
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Timer must be digit only ...")
            msg.setWindowTitle("Timer Input Error")
            msg.exec_()
            return
        if int(self.timer) > 3600 or int(self.timer) < 1: # beyond boudaries
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Range of Timer is [1, 3600] seconds ...")
            msg.setWindowTitle("Timer Input Error")
            msg.exec_()
            return
        # Must select cities
        if len(self.selected_cities) == 0:
            msg.setIcon(QMessageBox.Warning)
            msg.setText("You must add a city.")
            msg.setWindowTitle("City Empty Error")
            msg.exec_()
            return
        """
        (2) Change components' state
        """
        # disable components
        self.confirm_button.setText("Start observing h2s ...")  # 更改按钮上的文字
        self.confirm_button.setEnabled(False)  # 禁用按钮
        joined_string = ', '.join(self.selected_cities)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)  
        msg.setText("Successfully! Chosen cities: " + joined_string)  #
        msg.setWindowTitle("Success.")  
        msg.exec_()
        self.sender_email_input.setEnabled(False)
        self.receiver_email_input.setEnabled(False)
        self.password_input.setEnabled(False)
        self.timer_input.setEnabled(False)
        self.add_button.setEnabled(False)
        self.city_list_widget.setEnabled(False)
        self.remove_button.setEnabled(False)
        self.city_combo_box.setEnabled(False)
        self.url_input.setEnabled(False)
        self.tg_api_token_input.setEnabled(False)
        self.tg_chat_id_input.setEnabled(False)
        
        """
        (2) Save user_info whenever you click confirm button
        """
        self.save_user_info(self.sender_email, self.receiver_email, self.timer, self.selected_cities, self.tg_api_token, self.tg_chat_id)

        """
        (3) Change components' state
        """
        self.my_thread = ScheduleObserver(
            self.sender_email,
            self.receiver_email,
            self.password,
            self.selected_cities,
            is_valid_email(self.sender_email_input.text()),
            self.timer,
            self.url,
            self.tg_api_token,
            self.tg_chat_id,
            self.does_send_to_telegram
        )
        self.init_house_json_data()
        self.my_thread.start()

    def initUI(self):
        self.selected_cities = []
        layout = QVBoxLayout()
        self.resize(400, 300)  # window size
        # font = QFont("Arial", 14)  # font size
        # Telegram info : token
        self.tg_api_token_input = QLineEdit()
        layout.addWidget(QLabel("API-Token (Only applied for tg):"))
        layout.addWidget(self.tg_api_token_input)
        # Telegram info : chat-id
        self.tg_chat_id_input = QLineEdit()
        layout.addWidget(QLabel("Chat-Id (Only applied for tg):"))
        layout.addWidget(self.tg_chat_id_input)
        # Sender
        self.sender_email_input = QLineEdit()
        layout.addWidget(QLabel("Sender Email:"))
        layout.addWidget(self.sender_email_input)
        # Receiver
        self.receiver_email_input = QLineEdit()
        layout.addWidget(QLabel("Receiver Email:"))
        layout.addWidget(self.receiver_email_input)
        # Password
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(QLabel("Sender Email's Password:"))
        layout.addWidget(self.password_input)
        # Timer
        self.timer_input = QLineEdit()
        layout.addWidget(QLabel("Timer (1 -> 3600 seconds):"))
        layout.addWidget(self.timer_input)
        # Combo-box
        self.city_combo_box = QComboBox()
        for city_name in script.all_cities:
            self.city_combo_box.addItem(city_name)
        layout.addWidget(QLabel("Choose the city you care about"))
        layout.addWidget(self.city_combo_box)
        # Add-city button
        self.add_button = QPushButton("Add a city")
        self.add_button.clicked.connect(self.add_city)
        layout.addWidget(self.add_button)
        # List widget for showing cities chosen
        self.city_list_widget = QListWidget()
        layout.addWidget(self.city_list_widget)
        # Remove-city button
        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self.remove_selected_city)
        layout.addWidget(self.remove_button)
        # Confirm button
        self.confirm_button = QPushButton("Observe")
        self.confirm_button.clicked.connect(self.click_observe_button)
        layout.addWidget(self.confirm_button)
        self.setLayout(layout)
        self.url_input = QLineEdit()
        layout.addWidget(QLabel("URL (Optional: Wrong URL will crash): "))
        layout.addWidget(self.url_input)
        """
        Load user_info json data if user_info exists
        """
        user_info = self.load_user_info()
        if user_info:
            self.sender_email_input.setText(user_info['sender_email'])
            self.receiver_email_input.setText(user_info['receiver_email'])
            self.timer_input.setText(user_info['timer'])
            self.selected_cities = user_info['selected_cities']
            for city_name in self.selected_cities:
                self.city_list_widget.addItem(city_name)

    def init_house_json_data(self):
        json_data = dict()
        for city_name in script.all_cities:
            json_data[city_name] = 0
        json_data['Available'] = 0
        with open(house_json_file_name, 'w') as f:
            json.dump(json_data, f)
    
    def does_house_json_data_valid(self):
        # exist && has content
        return os.path.exists(house_json_file_name) and os.path.getsize(house_json_file_name) > 0
    
    def save_user_info(self, sender, receiver, timer, selected_cities, token, chat_id):
        self.user_info = {
            'sender_email': sender,
            'receiver_email': receiver,
            'timer': timer,
            'selected_cities': selected_cities,
            'token': token,
            'chat_id': chat_id
        }
        with open('user_info.json', 'w') as f:
            json.dump(self.user_info, f)
    
    def __get_user_info(self):
        with open('user_info.json', 'r') as f:
            return json.load(f)
    
    def load_user_info(self):
        if self.check_user_info():
            return self.__get_user_info()
        return None

    def check_user_info(self):
        return os.path.exists('user_info.json') and os.path.getsize('user_info.json') > 0
        
    def add_city(self):
        self.selected_city = self.city_combo_box.currentText()
        if self.selected_city:  # 确保选择了一个城市
            if self.selected_city not in self.selected_cities:  # 检查城市是否已经在列表中
                self.selected_cities.append(self.selected_city)  # 将新城市添加到列表中
                self.city_list_widget.addItem(self.selected_city)  # 将新城市添加到界面的列表控件中
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Duplicate city chosen. Please try again ...")
                msg.setWindowTitle("Duplicate City Error")
                msg.exec_()
                return

    def remove_selected_city(self):
        selected_items = self.city_list_widget.selectedItems()
        for item in selected_items:
            city_name = item.text()  # 获取列表项的文本（即城市名称）
            if city_name in self.selected_cities:  # 如果城市在 selected_cities 列表中
                self.selected_cities.remove(city_name)  # 从 selected_cities 列表中移除该城市
            self.city_list_widget.takeItem(self.city_list_widget.row(item))  # 从 QListWidget 中移除该城市

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())