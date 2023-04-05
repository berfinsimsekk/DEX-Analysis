import json

from pkg_resources import require
from web3 import Web3
from web3.middleware import geth_poa_middleware
from uniswap_universal_router_decoder import RouterCodec
import requests
import csv
from web3.contract import Contract

w3 =  Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/59371559ce134cbb851f7177a3aead75'))

latest_block = w3.eth.block_number
latest_block_object = w3.eth.get_block(latest_block, full_transactions=True)
transactions = latest_block_object['transactions']


tx_receipt = w3.eth.get_block('latest')


w3 =  Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/59371559ce134cbb851f7177a3aead75'))
codec = RouterCodec(w3=w3)
latest_block = w3.eth.block_number
start_block = max(0, latest_block - 2) # Get the block number 1000 blocks ago
count = 0

header = ['tx hash', 'permit', 'token', 'amount', 'exact in', 'amountIn', 'inPath','exact out', 'amountOut','outPath']



transactionList = []

for block_num in range(latest_block, start_block-1, -1):
    block = w3.eth.get_block(block_num, full_transactions=True)
    transactions = block['transactions']
    for tx in transactions:
        input_data = tx['input']
        if input_data.startswith('0x3593564c'):
            permit = "----"
            exact_in = "----"
            exact_out = "----"
            token=""
            amount=""
            amountIn=""
            inPath=""
            amountOut=""
            outPath=""
            count += 1

            decoded_transaction = codec.decode.transaction(tx['hash'].hex())
            tx_hash = tx['hash'].hex()
            inputs = decoded_transaction['decoded_input']['inputs']
            # Convert bytes string to hexadecimal format
            for input in inputs:
                if "PERMIT" in str(input[0]):
                    token = input[1]["struct"]["details"]["token"]
                    amount = input[1]["struct"]["details"]["amount"]
                    permit = "++++"
                elif "V3_SWAP_EXACT_IN" in str(input[0]) :
                    exact_in= "++++"
                    amountIn = input[1]["amountIn"]

                    if type(input[1]["path"]) is not list:
                        inPath = codec.decode.v3_path("V3_SWAP_EXACT_IN", input[1]["path"])
                    else:
                        inPath = input[1]["path"]

                elif "V3_SWAP_EXACT_OUT" in str(input[0]):
                    exact_out ="++++"
                    amountOut = input[1]["amountOut"]
                    if type(input[1]["path"]) is not list:
                        outPath = codec.decode.v3_path("V3_SWAP_EXACT_OUT", input[1]["path"])
                    else:
                        outPath = input[1]["path"]

                elif "V2_SWAP_EXACT_IN" in str(input[0]) :
                    exact_in= "++++"
                    amountIn = input[1]["amountIn"]
                    inPath = input[1]["path"]

                elif "V2_SWAP_EXACT_OUT" in str(input[0]) :
                    exact_out= "++++"
                    amountOut = input[1]["amountOut"]
                    outPath = input[1]["path"]

            lst = []
            lst.append(str(tx_hash))
            lst.append(str(permit))
            lst.append(str(token))
            lst.append(str(amount))
            lst.append(str(exact_in))
            lst.append(str(amountIn))
            lst.append(str(inPath))
            lst.append(str(exact_out))
            lst.append(str(amountOut))
            lst.append(str(outPath))
            transactionList.append(lst)


print("Total transactions with input starting with '0x3593564c':", count)
with open('data.csv', 'w', encoding='UTF8', newline='') as f:
    writer = csv.writer(f)

    # write the header
    writer.writerow(header)
    for l in transactionList:
        writer.writerow(l)



def getTheNameOfAToken(address):
    web3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/eth'))

    abi = [{"inputs": [], "name": "name", "outputs": [{"internalType": "string", "name": "", "type": "string"}],
            "stateMutability": "view", "type": "function"},
           {"inputs": [], "name": "symbol", "outputs": [{"internalType": "string", "name": "", "type": "string"}],
            "stateMutability": "view", "type": "function"}]

    contract = web3.eth.contract(address, abi=abi)

    token_name = contract.functions.name().call()
    token_symbol = contract.functions.symbol().call()

    return token_name

