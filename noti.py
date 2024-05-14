import requests
import time
from io import StringIO
from prettytable import PrettyTable
import pandas as pd
import discord_notify as dn
import bittensor.subtensor as st

burn_map = {}
reward_map = {}

# TODO: Update params
emission_netuids = [x] # example: [2, 7, 33]
my_netuids = [x] # example: [31, 7]
cold_keys = [
    'x'
]
follow_cold_keys = [
    'x'
] # Some one coldkey on same subnet
tele_chat_id = 'x'
tele_price_token = 'x'
tele_report_token = 'x'
notifier = dn.Notifier('x')
# End of update area


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
    for netuid in my_netuids:
        string, has_change = get_subnet_reward(netuid, follow_cold_keys, rewards)
        if has_change:
            need_send = True
        if string != '':
            text += f'\nNetuid: {netuid}* <pre>{string}</pre>'

    data = {
        "chat_id": tele_chat_id,
        "text": f'\nNEW ROUND: <pre>{text}</pre>',
        "parse_mode": "HTML"
    }


    requests.post(
        f'https://api.telegram.org/bot{tele_report_token}/sendMessage',
        json=data)
    
def get_emission():
    # Create an instance of the Subtensor class
    subtensor_instance = st(network='finney')
    
    # Get the metagraph information for all subnets
    response = subtensor_instance.get_all_subnets_info()
    
    # Extract netuid, emission_value, and burn for each subnet in the whitelist
    emissions_info = [
        (
            subnet_info.netuid,
            subnet_info.emission_value / 10000000,  # Convert to percentage
            subnet_info.burn
        )
        for subnet_info in response
        if subnet_info.netuid in emission_netuids
    ]
    
    # Print the emissions information for the whitelisted netUIDs
    x = PrettyTable()
    x.field_names = ['NetUID', 'Emission (%)', 'Burn']
    for netuid, emission, burn in emissions_info:
        x.add_row([netuid, emission, burn])
    data = {
        "chat_id": tele_chat_id,
        "text": f'<pre>{x.get_string()}</pre>',
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
            text += f'\nNetuid: {netuid} ```{string}```'  # Removed <pre> tags for Discord
    text += f'\nTotal: {sum(rewards)}'

    data = {
        "content": text
    }

    # Send the message to Discord using webhoo
    notifier.send(text, print_message=True)

def main():
    while True:
        time.sleep(3600)
        get_emission()
        send_report()
        # send_report_discord()

if __name__ == "__main__":
    main()
