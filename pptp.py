from os import path

import json
import os
import sys

network_manager_dir = "/etc/NetworkManager/system-connections/"

vpn_file = sys.argv[1]
vpn_file = path.abspath(vpn_file)
with open(vpn_file) as file:
    vpn_list = json.load(file)

passwd_file = sys.argv[2] if len(sys.argv) == 3 else 'passwd'
passwd_file = path.abspath(passwd_file)
with open(passwd_file) as file:
    username, password = file.read().split('\n')

countries_number_of_vpns = dict()
for vpn in vpn_list:
    vip = '.vip' if 'vip' in vpn_file else ''
    country = vpn['country']
    gateway = vpn['address']

    if country in countries_number_of_vpns:
        countries_number_of_vpns[country] += 1
        number = countries_number_of_vpns[country]
    else:
        countries_number_of_vpns[country] = 1
        number = 1

    os.system(f"nmcli con add con-name vpn.{country}{f'.{number}'}{vip} ifname \"*\" type vpn vpn.service-type pptp")

    with open(path.join(network_manager_dir, f'vpn.{country}{f".{number}"}{vip}.nmconnection')) as file:
        raw_data = file.read().split('\n')

    section = ''
    kwargs = dict()  # line-number -> list of data-to-append
    for line_itr, line in enumerate(raw_data):
        if line == '':
            continue

        if line[0] == '[' and line[-1] == [']']:
            section = line

        if section == '[vpn]':
            kwargs[line_itr] = [
                f'gateway={gateway}',
                f'password-flags=0',
                f'user={username}'
            ]

        if section == '[ipv4]':
            kwargs[line_itr - 1] = [
                f'\n'
                f'[vpn-secrets]\n'
                f'password={password}'
            ]

    data = str()
    for line_itr, line in enumerate(raw_data):
        if line_itr in kwargs:
            for extra in kwargs[line_itr]:
                data += extra + '\n'

        data += line + '\n'

    with open(path.join(network_manager_dir, f'vpn.{country}{f".{number}"}{vip}.nmconnection'), 'w') as file:
        file.write(data)


def convert_server_txt_to_json(servers_dir: str):
    for each in list(map(path.abspath, os.listdir(servers_dir))):
        if path.isfile(each) and each[:-len('.txt')] == '.txt':

            with open(each) as f:
                txt_data = f.read()

            servers = list(map(
                lambda x: [' '.join(x.split(' ')[:-1]), x.split(' ')[-1]], txt_data.replace('\t', ' ').split('\n')
            ))
            json_data = [{"country": server[0], "address": server[1]} for server in servers]

            json_file_name = each[:each.rfind('.txt')] + '.json'
            with open(json_file_name, 'w') as f:
                json.dump(json_data, f)

            if path.exists(each) and path.isfile(each):
                os.remove(path.join(os.getcwd(), each))
