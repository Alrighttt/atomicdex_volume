# partial_volume.py

This script will iterate backwards over each block on `ALICE_CHAIN` until it reaches the specified timestamp, `start_time`. It will find each transaction that has a p2sh vout then find the transaction that spends this vout, `spent_tx`(if it exists). With `spent_tx`, we can look at the scriptsig of it's vin and find the "mutual secret" that can be used to associate these two transactions with the two corresponding transactions on `BOB_CHAIN`. 

Total volume and total number of succesful swaps will be shown in stdout. The txids of each swap will be saved to `<ALICE_CHAIN>_<BOB_CHAIN>_partial.json`. 

Please note that this script isn't able to distinguish between maker and taker.

`start_time` variable can be changed to whatever fits your needs. The script asks for amount of previous days just to simplify usage.

Usage:
```
./partial_volume.py RICK MORTY
Please input amount of previous days: 7
RICK volume: 63.93462397
MORTY volume: 55.02253751
total succesful swaps: 35
```


# volume.py

This script will scrape both chains for all p2sh transactions of addresses asscioated with the DEX fee address. Alice is associated by sending the dex fee to it. Bob is associated by trading with Alice. 

This script can take an incredibly long amount of time. It's recommended to only run this once to initialize a database. After that use `partial_volume.py` to update the db incrementally. 
