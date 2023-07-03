# CrawlDefiHackLabs
The goal is to crawl the DefiHackLabs repository and restructure the PoC in a more effective and useful manner.

# Head Commit
[1df141b3cb0d017c7d3cd0ef4ca4979516d30d8e](https://github.com/SunWeb3Sec/DeFiHackLabs/tree/1df141b3cb0d017c7d3cd0ef4ca4979516d30d8e)

# Apply Patch
```
git submodule init
git submodule update
cd DeFiHackLabs
git apply ../crawl.diff
```

# Solidity Grammar
Install antlr4
Replace `Solidity.g4` with https://github.com/antlr/grammars-v4/blob/master/solidity/Solidity.g4



# Dataset Info
Larger Than 4096 Tokens: 10

- 29252e856c 6324
- d11fac3443 12278
- 643f7d2e3c 5085
- 68ddf64f09 5993
- cf8e54db67 4112
- 5b30b35fa5 5059
- 69390e6b84 6030
- 2c48132827 9589
- 61046d37d1 4659
- 02fc2091ed 4437

Test Case Tokens: 326_527

Number of Test Cases: 233

# TODOs
- [ ] Update files to store in csv/plaintext instead of json.
- [ ] Update ChatGPT prompt.
- [ ] Create the train/eval dataset --> (interface, vuln, testcase, explain).
- [ ] Check if more properties are needed?


""
