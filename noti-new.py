import requests
import time
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
    x.field_names = ["UID", "EMISSION", "REWARDS", "RANK"]

    url = 'https://api.subquery.network/sq/TaoStats/bittensor-subnets'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0', 'Accept': '*/*', 'Accept-Language': 'vi-VN,vi;q=0.8,en-US;q=0.5,en;q=0.3', 'Accept-Encoding': 'gzip, deflate, br', 'Referer': 'https://x.taostats.io/', 'Content-Type': 'application/json', 'Origin': 'https://x.taostats.io', 'DNT': '1', 'Connection': 'keep-alive', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'cross-site', 'TE': 'trailers'}
    page = 0
    nodes = []
    while page < 1:
        data = {"query": "query ($first: Int!, $offset: Int!, $filter: NeuronInfoFilter, $order: [NeuronInfosOrderBy!]!) { neuronInfos(first: $first, offset: $offset, filter: $filter, orderBy: $order) { nodes { coldkey dailyReward emission uid } pageInfo { endCursor hasNextPage hasPreviousPage } totalCount } }", "variables": {"offset": page * 100, "first": 256, "filter": {"netUid": {"equalTo": netuid}}, "order": "EMISSION_ASC"}}
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()
        nodes += response_data.get("data", {}).get("neuronInfos", {}).get("nodes", [])
        page += 1
    
    df = pd.DataFrame(nodes)
    df['dailyReward'] = df['dailyReward'].astype(float)
    df['emission'] = df['emission'].astype(float)

    emissions = df['emission']
    has_change = False
    df = df[df['coldkey'].isin(cold_keys)]
    if df.empty:
        return '', has_change
    emissions = emissions[emissions > 0]

    for index, row in df.iterrows():
        key = f'{netuid}_{row["uid"]}'
        arrow = ''
        if key in reward_map:
            if reward_map[key] > row['dailyReward']:
                arrow = '↓'
                has_change = True
            elif reward_map[key] < row['dailyReward']:
                arrow = '↑'
                has_change = True
        else:
            has_change = True

        reward_map[key] = row['dailyReward']
        x.add_row([
            row['uid'],
            '{0:.5f}'.format(round(row['emission'] / 1000000000, 5)),
            '{0:.3f}'.format(round(row['dailyReward'] / 1000000000, 3)) + arrow,
            emissions[emissions < row['emission']].count() + 1
        ])
        rewards.append(row['dailyReward'])

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
    text += f'\nTotal: {sum(rewards)/1000000000}'
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
    text += f'\nTotal: {sum(rewards)/1000000000}'

    data = {
        "content": text
    }

    # Send the message to Discord using webhoo
    notifier.send(text, print_message=True)

def main():
    while True:
        time.sleep(3600)
        send_report()
        get_emission()
        send_report_discord()

if __name__ == "__main__":
    main()
