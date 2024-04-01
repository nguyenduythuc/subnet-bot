import requests
import time
from io import StringIO
from prettytable import PrettyTable
import pandas as pd
import discord_notify as dn

burn_map = {}
my_netuids = [7, 32]
cold_keys = [
    'xxx'
]
tele_chat_id = 'xxx'
tele_price_token = 'xxx'
tele_report_token = 'xxx'
notifier = dn.Notifier('xxx')
reward_map = {}

hotkeys = {
    'hk1': 'xxx',
    'hk2': 'xxx',
    'hk3': 'xxx',
}


def get_subnet_reward(netuid, cold_keys, rewards):
    x = PrettyTable()
    x.field_names = ["UID", "INCENTIVE", "REWARDS", "RANK"]
    url = 'https://taostats.io/wp-admin/admin-ajax.php'
    data = {
        'action': 'metagraph_table',
        'this_netuid': netuid
    }

    response = requests.post(url, data=data)
    tables = pd.read_html(StringIO(response.text))
    df = tables[0].sort_values(by='INCENTIVE', ascending=True)
    incentives = df['INCENTIVE']

    has_change = False
    df = df[df['COLDKEY'].isin(cold_keys)]
    if df.empty:
        return '', has_change

    incentives = incentives[incentives > 0]

    for index, row in df.iterrows():
        key = f'{netuid}_{row["UID"]}'
        arrow = ''
        if key in reward_map:
            if reward_map[key] > row['DAILY REWARDS']:
                arrow = '↓'
                has_change = True
            elif reward_map[key] < row['DAILY REWARDS']:
                arrow = '↑'
                has_change = True
        else:
            has_change = True

        reward_map[key] = row['DAILY REWARDS']
        x.add_row([row['UID'], row['INCENTIVE'],
                   '{0:.3f}'.format(row['DAILY REWARDS']) + arrow,
                   incentives[incentives < row['INCENTIVE']].count() + 1])
        rewards.append(row['DAILY REWARDS'])

    return x.get_string(), has_change


def send_report():
    text = ''
    rewards = []
    need_send = False
    for netuid in my_netuids:
        string, has_change = get_subnet_reward(netuid, cold_keys, rewards)
        if has_change:
            need_send = True
        if string != '':
            text += f'\nNetuid: {netuid} <pre>{string}</pre>'
    text += f'\nTotal: {sum(rewards)}'

    data = {
        "chat_id": tele_chat_id,
        "text": text,
        "parse_mode": "HTML"
    }


    requests.post(
        f'https://api.telegram.org/bot{tele_report_token}/sendMessage',
        json=data)

def send_report_discord():
    text = ''
    rewards = []
    need_send = False
    for netuid in my_netuids:
        string, has_change = get_subnet_reward(netuid, cold_keys, rewards)
        if has_change:
            need_send = True
        if string != '':
            text += f'\nNetuid: {netuid} {string}'  # Removed <pre> tags for Discord
    text += f'\nTotal: {sum(rewards)}'

    data = {
        "content": text
    }

    # Send the message to Discord using webhoo
    notifier.send(text, print_message=True)

def main():
    while True:
        # try:
        send_report_discord()
        # except Exception as e:
            # print(f"Error sending Discord report: {e}")
        send_report()
        print(f"Error sending Discord report")
        time.sleep(3600)

if __name__ == "__main__":
    main()

# pm2 start python3 --name tele_noti -- ./noti.py