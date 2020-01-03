#!/usr/bin/env python3
import requests
import time
import platform
import os
import re
import json
import sys
from slickrpc import Proxy



# define data dir
def def_data_dir():
    operating_system = platform.system()
    if operating_system == 'Darwin':
        ac_dir = os.environ['HOME'] + '/Library/Application Support/Komodo'
    elif operating_system == 'Linux':
        ac_dir = os.environ['HOME'] + '/.komodo'
    elif operating_system == 'Windows':
        ac_dir = '%s/komodo/' % os.environ['APPDATA']
    return(ac_dir)


# fucntion to define rpc_connection
def def_credentials(chain):
    rpcport = '';
    ac_dir = def_data_dir()
    if chain == 'KMD':
        coin_config_file = str(ac_dir + '/komodo.conf')
    else:
        coin_config_file = str(ac_dir + '/' + chain + '/' + chain + '.conf')
    with open(coin_config_file, 'r') as f:
        for line in f:
            l = line.rstrip()
            if re.search('rpcuser', l):
                rpcuser = l.replace('rpcuser=', '')
            elif re.search('rpcpassword', l):
                rpcpassword = l.replace('rpcpassword=', '')
            elif re.search('rpcport', l):
                rpcport = l.replace('rpcport=', '')
    if len(rpcport) == 0:
        if chain == 'KMD':
            rpcport = 7771
        else:
            print("rpcport not in conf file, exiting")
            print("check " + coin_config_file)
            exit(1)

    return (Proxy("http://%s:%s@127.0.0.1:%d" % (rpcuser, rpcpassword, int(rpcport))))

# this should be used instead of all_p2sh if you don't need all historical swaps
def some_p2sh(rpc, timestamp):
    getinfo = rpc.getinfo()
    height = getinfo['blocks']
    tip_time = getinfo['tiptime']
    all_tx = []
    while tip_time > timestamp:
        block = rpc.getblock(str(height), 2)
        all_tx += block['tx']
        height -= 1
        tip_time = block['time']
    txids = []
    for tx in all_tx:
        for vout in tx['vout']:
            if vout['scriptPubKey']['type'] == 'scripthash':
                txids.append([tx['txid'], vout['n']])
    return(txids)

# find scriptsig that should be mutual between alice and bob
def mutual_scripts(rpc, txids):
    mutuals = {}
    for txid in txids:
        tx = rpc.getrawtransaction(txid[0], 1)
        if 'spentTxId' in tx['vout'][txid[1]]:
            spent_txid = tx['vout'][txid[1]]['spentTxId']
        else: # this can pick up failed or in progress 2/5 or 3/5 swaps if desired
            continue 
        spent_tx = rpc.getrawtransaction(spent_txid, 2)
        bob_addr = spent_tx['vout'][0]['scriptPubKey']['addresses'][0]
        mutual = spent_tx['vin'][0]['scriptSig']['hex'][-284:-220]
        if len(mutual) == 64:
            mutuals[mutual] = [[txid[0], tx['vout'][txid[1]]['valueSat']], [spent_txid, spent_tx['vout'][0]['valueSat']]]

    return(mutuals)

ALICE_CHAIN = sys.argv[1]
BOB_CHAIN = sys.argv[2]
ALICE_RPC = def_credentials(ALICE_CHAIN)
BOB_RPC = def_credentials(BOB_CHAIN)

try:
    days = int(input('Please input amount of previous days: '))
except:
    sys.exit('days must be whole number')

now = int(time.time())
start_time = now - days*86400

alice_p2sh = some_p2sh(ALICE_RPC, start_time)
bob_p2sh = some_p2sh(BOB_RPC, start_time)

alice_mutuals = mutual_scripts(ALICE_RPC, alice_p2sh)
bob_mutuals = mutual_scripts(BOB_RPC, bob_p2sh)

swaps = []
for bob_mutual in bob_mutuals:
    if bob_mutual in alice_mutuals:
        swap = {
        "1_alice_b": alice_mutuals[bob_mutual][0],
        "2_bob_b": bob_mutuals[bob_mutual][0],
        "3_b_alice": alice_mutuals[bob_mutual][1],
        "4_b_bob": bob_mutuals[bob_mutual][1]
        }
        swaps.append(swap)

f = open(ALICE_CHAIN + "_" + BOB_CHAIN + "_24hr.json", "w+")
f.write(json.dumps(swaps))

alice_vol = 0
bob_vol = 0
for swap in swaps:
    alice_vol += swap['1_alice_b'][1]
    bob_vol += swap['2_bob_b'][1]

print(ALICE_CHAIN + ' volume:', alice_vol/100000000)
print(BOB_CHAIN + ' volume:', bob_vol/100000000)
print('total succesful swaps:', len(swaps))