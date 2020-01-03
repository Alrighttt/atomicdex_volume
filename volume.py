#!/usr/bin/env python3
import requests
import time
import platform
import os
import re
import json
import pprint # FIXME
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


# find all p2sh transactions of addresses asscociated with DEX fee address
# doing this in daemon will speed this script up significantly
def all_p2sh(rpc, addrs):
    DEX_txids = rpc.getaddresstxids({"addresses": ['RThtXup6Zo7LZAi8kRWgjAyi1s4u6U9Cpf']}) # DEX fee address
    for txid in DEX_txids:
        tx = rpc.getrawtransaction(txid, 2)
        if tx['vin'][0]['address'] not in addrs:
            addrs.append(tx['vin'][0]['address']) 
    try: # dpow addr needs to be removed or getaddresstxids will time out 
        addrs.remove('RXL3YXG2ceaB6C5hfJcN4fvmLH2C34knhA')
    except:
        pass
    all_alice_txids = rpc.getaddresstxids({"addresses": addrs})
    p2sh_txids = []

    count = 0
    total = len(all_alice_txids)
    for txid in all_alice_txids:
        count += 1 
        print('ALL TXIDS COUNT', count)
        print('TOTAL', total)
        print('\n')
        tx = rpc.getrawtransaction(txid, 2)
        for vout in tx['vout']:
            if vout['scriptPubKey']['type'] == 'scripthash':
                p2sh_txids.append([txid, vout['n']])
    return(p2sh_txids)


# find scriptsig that should be mutual between alice and bob
def mutual_scripts(rpc, txids):
    mutuals = {}
    addrs = []
    for txid in txids:
        tx = rpc.getrawtransaction(txid[0], 2)
        if 'spentTxId' in tx['vout'][txid[1]]:
            spent_txid = tx['vout'][txid[1]]['spentTxId']
        else: # this can pick up failed or in progress 2/5 or 3/5 swaps if desired
            continue 
        spent_tx = rpc.getrawtransaction(spent_txid, 2)
        bob_addr = spent_tx['vout'][0]['scriptPubKey']['addresses'][0]
        if bob_addr not in addrs:
            addrs.append(bob_addr)
        mutual = spent_tx['vin'][0]['scriptSig']['hex'][-284:-220]
        if len(mutual) == 64:
            mutuals[mutual] = [txid[0], spent_txid]

    return(mutuals, addrs)

    
ALICE_CHAIN = 'KMD'
BOB_CHAIN = 'LABS'
ALICE_RPC = def_credentials(ALICE_CHAIN)
BOB_RPC = def_credentials(BOB_CHAIN)

alice_p2sh = all_p2sh(ALICE_RPC, [])
alice_mutuals, bob_addrs = mutual_scripts(ALICE_RPC, alice_p2sh)

bob_p2sh = all_p2sh(BOB_RPC, bob_addrs)
bob_mutuals, alice_addrs = mutual_scripts(BOB_RPC, bob_p2sh)

swaps = []
print('bob mutuals len', len(bob_mutuals))
print('alice mutuals len', len(alice_mutuals))


for bob_mutual in bob_mutuals:
    if bob_mutual in alice_mutuals:
        swap = {
        "1_alice_b": alice_mutuals[bob_mutual][0],
        "2_bob_b": bob_mutuals[bob_mutual][0],
        "3_b_alice": alice_mutuals[bob_mutual][1],
        "4_b_bob": bob_mutuals[bob_mutual][1]
        }
        swaps.append(swap)

f = open(ALICE_CHAIN + "_" + BOB_CHAIN + ".json", "w+")
f.write(json.dumps(swaps))

print(len(swaps))