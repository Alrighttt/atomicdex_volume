#!/usr/bin/env python3
import requests
import time
import platform
import os
import re
import json
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
    

# given DEX transaction, find alice address and alice->b txid if it exists
def find_alice(rpc, txid):
    tx = rpc.getrawtransaction(txid, 2)
    invalid = [False, False, False]
    # FIXME add as many checks as possible here to narrow down if it's mm2 tx
    # can check script of vins/vouts
    # can hardcode chain specific heights to start at
    # can check via timestamp
    # can check txfee if it's standard
    if tx['version'] != 4:
        return(invalid)
    if len(tx['vin']) != 1:
        return(invalid)
    if len(tx['vout']) != 2:
        return(invalid)
        
    # FIX ME if dex fee is not 1/777*alice_b, bob chain IS KMD
    
    try:
        alice_b = tx['vout'][1]['spentTxId']
    except:
        alice_b = False
    # this can fail because of non-mm2 txes sent to DEX address
    # safely ignored
    try:
        return([tx['vout'][1]['scriptPubKey']['addresses'][0], alice_b, tx['vout'][0]['valueSat']])
    except Exception as e:
        return(invalid)

#given alice->b txid, find bob address, alice volume, b_bob tx and mutual script
def find_bob(rpc, txid):
    invalid = [False,False,False,False]
    alice_b_tx = rpc.getrawtransaction(txid, 2)
    try:
        b_bob_txid = alice_b_tx['vout'][0]['spentTxId']
        vout_index = alice_b_tx['vout'][0]['spentIndex']
    except Exception as e:
        return(invalid)
    b_bob_tx = rpc.getrawtransaction(b_bob_txid, 2)
    
    # this can fail because of non-mm2 txes sent to DEX address
    # safely ignored
    try:
        bob_addr = b_bob_tx['vout'][vout_index]['scriptPubKey']['addresses'][0]
        volume = alice_b_tx['vout'][0]['valueSat']
        # FIXME need to be 100% sure this value is in static position
        script = b_bob_tx['vin'][0]['scriptSig']['hex'][-284:-220]
    except Exception as e:
        #print(e)
        return(invalid)
    return([bob_addr, volume, b_bob_txid, script])

    
ALICE_CHAIN = 'MORTY'
BOB_CHAIN = 'RICK'
ALICE_RPC = def_credentials(ALICE_CHAIN)
BOB_RPC = def_credentials(BOB_CHAIN)
DEX = 'RThtXup6Zo7LZAi8kRWgjAyi1s4u6U9Cpf'
DEX_txids = ALICE_RPC.getaddresstxids({"addresses": [DEX]})

#highest = [0,0,0]
amount_total = 0
swaps = []
# -amount of previous DEX fee addr txes
for txid in DEX_txids[-10000:]:
    alice_addr, alice_b, fee_amount = find_alice(ALICE_RPC, txid)
    if alice_b:
        bob_addr, volume, b_bob, script = find_bob(ALICE_RPC, alice_b)
        if bob_addr:
            swap = {
                    'alice_addr':alice_addr,
                    'bob_addr':bob_addr,
                    'script': script,
                    '0_fee_txid': [txid, fee_amount],
                    '1_alice_b': [alice_b, volume],  
                    '3_b_bob': [b_bob]
                    }
            if swap not in swaps:
                swaps.append(swap)
            # this if can be removed, just tracks the highest volume swap
            #if fee_amount > highest[0]:
            #    highest = [fee_amount,txid, bob_addr, alice_addr]
            #amount_total += fee_amount

completed_swaps = []

# populate all alices getaddresstxids
address_txids = {}
for swap in swaps:
    alice_txids = []
    if swap['alice_addr'] not in address_txids:
        alice_txids = BOB_RPC.getaddresstxids({"addresses": [swap['alice_addr']]})
        address_txids[swap['alice_addr']] = alice_txids

for swap in swaps:
    for alice_txid in address_txids[swap['alice_addr']]:
        tx = BOB_RPC.getrawtransaction(alice_txid, 2)
        # FIXME need to be 100% sure this value is in static position
        if tx['vin'][0]['scriptSig']['hex'][-284:-220] == swap['script']:
            swap['2_bob_b'] = [tx['vin'][0]['txid'], tx['vout'][0]['valueSat']]
            swap['4_b_alice'] = [alice_txid]
            completed_swaps.append(swap)
            address_txids[swap['alice_addr']].remove(alice_txid)
    
    
f = open(ALICE_CHAIN + "_" + BOB_CHAIN + ".json", "w+")
f.write(json.dumps(swaps))

f = open(ALICE_CHAIN + "_" + BOB_CHAIN + "_completed.json", "w+")
f.write(json.dumps(completed_swaps))

    
