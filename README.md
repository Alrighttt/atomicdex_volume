`pip3 install requests slick-bitcoinrpc`


This script will scrape the specified ALICE_CHAIN for "dex fee" transactions. From there it will find the corresponding swap txids on both chains if they exist. 

It will save all swap data to `<ALICE_CHAIN>_<BOB_CHAIN>.json` and completed swap data to `<ALICE_CHAIN>_<BOB_CHAIN>_completed.json`

Taking a look at the `<ALICE_CHAIN>_<BOB_CHAIN>.json` json, you will see swaps that have 0, 1 and 3 steps of the process. This means the swap took place on another pair. 
If you see swaps that go no further than 0 and 1, this indicates a failed or in progress swap. 

This script can take a long while (~25 minutes for a KMD pair). There are likely a dozen different ways to optimize this. This was simply an exercise to prove it's possible, and that it is reliable. 
