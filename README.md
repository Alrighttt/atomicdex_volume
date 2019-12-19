  This has proven to be an unreliable method to track volume. This is because this script assumes vout1 of the DEX fee transaction would always be spent in the alice->b_addr transaction. An example of a swap that would not be picked up by this script because of this bad assumption:
```
"ac33d501-8f1a-4f7c-b5ef-86fe5e33de50": {
  "TakerFeeValidated": "f59cef205f9aee385503f5e84a971b97163eed376323dd224647577763be24a8",
  "MakerPaymentSent": "e7e6c6538e6c119fe70443ced5d32ce7e8748ce221ffe072cf23509cabaed6cc",
  "TakerPaymentReceived": "737108f23243e0a7ec70df6988240952c4c76bd81476340e687144e5dc2e6dbb",
  "TakerPaymentSpent": "f54f805509e6198b7b5e073d06cc767ae6433c113263ad91f5ad50db6baa1522"
}
```

  Still trying to think how I can work around not being able to make this assumption. We must find a reliable way to find alice->b_addr transaction given the corresponding DEX fee transaction. 


`pip3 install requests slick-bitcoinrpc`


This script will scrape the specified ALICE_CHAIN for "dex fee" transactions. From there it will find the corresponding swap txids on both chains if they exist. It requires spent index and address index enabled on both chains. 

It will save all swap data to `<ALICE_CHAIN>_<BOB_CHAIN>.json` and completed swap data to `<ALICE_CHAIN>_<BOB_CHAIN>_completed.json`

Taking a look at the `<ALICE_CHAIN>_<BOB_CHAIN>.json` json, you will see swaps that have 0, 1 and 3 steps of the process. This means the swap took place on another pair. 
If you see swaps that go no further than 0 and 1, this indicates a failed or in progress swap. 

This script can take a long while (~25 minutes for a KMD pair). There are likely a dozen different ways to optimize this. This was simply an exercise to prove it's possible, and that it is reliable. 
