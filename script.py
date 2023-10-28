import requests
from bs4 import BeautifulSoup
import smtplib
import json

all_cities = [
    'Amsterdam', 
    'Arnhem', 
    'Capelle aan den IJssel', 
    'Delft',
    'Den Bosch',
    'Den Haag',
    'Diemen',
    'Dordrecht',
    'Eindhoven',
    'Groningen',
    'Haarlem',
    'Helmond',
    'Maarssen',
    'Maastricht',
    'Nijmegen',
    'Rotterdam',
    'Rijswijk',
    'Sittard',
    'Tilburg',
    'Utrecht',
    'Nieuwegein',
    'Zeist',
    'Zoetermeer']

# 抓取房源信息
def fetch_housing_data(url):
    import re
    response = requests.get(url)
    pattern = re.compile(r'([A-Za-z\s]+)\s+(\d+)')
    if response.status_code == 200:
        print(">>> Response: Success")
        housing_list_dict = dict()
        # parse data
        soup = BeautifulSoup(response.text, 'html.parser')
        # book directly
        dom_book_directly = soup.find('span', {'class': 'count'})
        count_book_directly = int(list(dom_book_directly.children)[0])  # '2'Z
        if count_book_directly == 0: return None, 0 # If not book directly houses shown ... return
        # print(count_book_directly)
        # cities
        # find all <ol> tags that include city's information
        cities_tag = soup.find('ol', {'class': 'items ln-items-city'}) # <ol>
        cities_item = cities_tag.find_all('li', {'class': 'item'}) # <li>
        # 遍历所有的 <li> 标签
        for idx, city in enumerate(cities_item):
            # print(idx, city)
            city_tag = city.find('a')  # 查找 <a> 标签
            if city_tag:
                city_tag_piece = city_tag.get_text().strip()
                match = pattern.search(city_tag_piece)
                # print(city_tag.get_text().strip())
                if match:
                    city_name = match.group(1).strip()
                else:
                    return None, 0
                    # items = match.group(2)
                    # print(f"City: {city}, Items: {items}")
                    # city_name = city_tag.get_text().split()[0].strip()  # 提取城市名，并去掉额外的空白
                # 查找包含房源数量的 <span> 标签
                cities_count = city_tag.find('span', {'class': 'count'})
                if cities_count:
                    cities_count = cities_count.contents[0].strip()  # 提取房源数量，并去掉额外的空白
                    cities_count = int(cities_count)  # 转换为整数
                    housing_list_dict.update({city_name: cities_count})
                    # print(f"City: {city_name}, Count: {cities_count}")

        print(">>> Cities available: ")
        for k, v in housing_list_dict.items():
            print("- " + k + ": " + str(v))
        # print(len(housing_list_dict))
        return housing_list_dict, count_book_directly
    else:
        print(">>> Response: Error")
        return None, 0

def check_and_update_data(new_house_data, init, old_house_data, selected_cities):
    current_updated_cities = dict()
    notify = False
    if init:
        for city_name, new_house_count in new_house_data.items():
            if old_house_data[city_name] != new_house_count:
                old_house_data[city_name] = new_house_count
    else:
        for city_name, old_house_count in old_house_data.items():
            """
            if house number is changed
            """
            old_house_count = old_house_data[city_name]
            if city_name in new_house_data:
                new_house_count = new_house_data[city_name]
                if old_house_data[city_name] != new_house_count:
                    old_house_data[city_name] = new_house_count
                    """
                    check if there is a need to send notification via email
                    """
                    if city_name in selected_cities: 
                        notify = True
                        current_updated_cities[city_name] = str(old_house_count) + " -> " + str(new_house_data[city_name]) + " (Now)"
                        print(f"- (*) House number updated for {city_name}: {old_house_count} -> {new_house_count}" + " (Now)")
                    else:
                        print(f"- House number updated for {city_name}: {old_house_count} -> {new_house_count}")
            elif city_name == 'Available': continue
            elif city_name not in new_house_data: # new is 0
                if old_house_count != 0:
                    if city_name in selected_cities:
                        notify = True
                        current_updated_cities[city_name] = str(old_house_count) + " -> " + str(0) + " (Now)"
                        print(f"- (*) House number updated for {city_name}: {old_house_count} -> {0}" + " (Now)")
                    else:
                        print(f"- House number updated for {city_name}: {old_house_count} -> {0}" + " (Now)")
                    old_house_data[city_name] = 0
        
    return old_house_data, current_updated_cities, notify

def save_to_json(filename, json_data):
    with open(filename, 'w') as f:
        json.dump(json_data, f)

def save_to_json_and_check_if_notify(
        new_house_data, 
        available_count, 
        selected_cities, 
        personal_info,):
    filename = "fetch_data.json"
    
    """
    (1) Read json, if there is no content in this json, initialize it then.
    """
    with open(filename, 'r') as f:
        json_data = json.load(f)
    init = True if sum(json_data.values()) == 0 else False
    """
    (2) Check and Save
    """
    # check and update data
    if json_data['Available'] != available_count:
        print(f">>> Book directly number updated : {json_data['Available']} -> {available_count}")
        json_data['Available'] = available_count
    print(">>> Selected cities: ", selected_cities)
    print(">>> Init: ", init)
    json_data, current_updated_cities, notify = check_and_update_data(new_house_data, init, json_data, selected_cities)
    # save data to json           
    save_to_json(filename, json_data)
    """
    check if there is a need to send notification via email
    """
    if notify:
        # for k, v in current_updated_cities.items():
        #     print(k, ",", str(v))
        if not personal_info['does_send_to_tg']:
            send_email(current_updated_cities, personal_info['sender'], personal_info['receiver'], personal_info['pwd'], personal_info['email_type'])
        else:
            send_tg(current_updated_cities, personal_info['token'], personal_info['chat_id'])
        print(">>> Data updated and started sending email ...")
    else:
        print(">>> Data updated but the city we care about hasn't changed ...")
    print()

def get_notification_content(current_updated_cities):
    subject = "!!!(H2S) New Housing Alert"
    body = "Updates on the number of the houses of your preferable cities:\n" 
    for city_name, change in current_updated_cities.items():
        body = body + city_name + ": " + change + "\n"
    return subject, body

def send_tg(current_updated_cities, token, chat_id):
    subject, body = get_notification_content(current_updated_cities)
    msg = f"Subject: {subject}\n\n{body}"
    send_text = f'https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&parse_mode=Markdown&text={msg}'
    import requests
    response = requests.get(send_text)
    if response.status_code == 200:
        print("Succeed to send msg to tg ...")
    else:
        print("Failed to send msg to tg ...")

# send email
def send_email(current_updated_cities, from_email, to_email, password, sender_email_type):

    # smtp_server = 'smtp.gmail.com' # Keep gmail according to from_email
    if sender_email_type == 'Microsoft':
        smtp_server = 'smtp.office365.com'
    elif  sender_email_type == 'Google':
        smtp_server = 'smtp.gmail.com'
    
    smtp_port = 587  # 587 是用于 STARTTLS 的标准端口

    # Email content
    subject, body = get_notification_content(current_updated_cities)
    
    # Sending
    server = smtplib.SMTP(smtp_server, smtp_port) 
    server.starttls()
    server.login(from_email, password)
    server.sendmail(from_email, to_email, f"Subject: {subject}\n\n{body}")
    server.quit()
    print(">>> Email sent successfully!")


def main(sender_email, 
         receiver_email, 
         password, 
         selected_cities, 
         sender_email_type, 
         token,
         chat_id,
         does_send_to_tg,
         url="https://holland2stay.com/residences.html?available_to_book=179"):

    print(">>>>>>>>>>>>>>>>>>>>> Try the observation" + " ... ")
    # url = "https://holland2stay.com/residences.html?available_to_book=179"
    # url = "https://holland2stay.com/residences.html?available_to_book=336"
    new_houses_data, count_book_directly = fetch_housing_data(url)
    if new_houses_data is None: 
        print("Data fetch is failed or no available houses currently ...")
        return
    personal_info = dict()
    if not does_send_to_tg:
        personal_info['sender'] = sender_email
        personal_info['receiver'] = receiver_email
        personal_info['pwd'] = password
        personal_info['email_type'] = sender_email_type
        personal_info['does_send_to_tg'] = False
    else:
        personal_info['token'] = token
        personal_info['chat_id'] = chat_id
        personal_info['does_send_to_tg'] = True

    save_to_json_and_check_if_notify(
        new_houses_data, 
        count_book_directly,  
        selected_cities,
        personal_info)