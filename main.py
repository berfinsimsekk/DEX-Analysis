from web3 import Web3
from uniswap_universal_router_decoder import RouterCodec
import csv
import webbrowser
import os
import ast
import sys
import time

st = time.time()

w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/59371559ce134cbb851f7177a3aead75'))
codec = RouterCodec(w3=w3)
block_count = int(sys.argv[1])
latest_block = w3.eth.block_number
start_block = max(0, latest_block - block_count)  # Get the block number 1000 blocks ago
count = 0

header = ['tx hash', 'permit', 'token', 'amount', 'exact in', 'amountIn', 'inPath', 'exact out', 'amountOut', 'outPath']

transactionList = []


def getTheNameOfAToken(address):
    web3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/eth'))

    if address == "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2":
        return "ETH"

    output = ""

    try:
        abi = [{"inputs": [], "name": "name", "outputs": [{"internalType": "string", "name": "", "type": "string"}],
                "stateMutability": "view", "type": "function"},
               {"inputs": [], "name": "symbol", "outputs": [{"internalType": "string", "name": "", "type": "string"}],
                "stateMutability": "view", "type": "function"}]
        contract = web3.eth.contract(address, abi=abi)

        token_name = contract.functions.name().call()
        token_symbol = contract.functions.symbol().call()

        output = token_name
    except:
        output = address

    return output


for block_num in range(latest_block, start_block - 1, -1):
    block = w3.eth.get_block(block_num, full_transactions=True)
    transactions = block['transactions']
    for tx in transactions:
        input_data = tx['input']
        if input_data.startswith('0x3593564c'):
            permit = "----"
            exact_in = "----"
            exact_out = "----"
            token = ""
            amount = ""
            amountIn = ""
            inPath = ""
            amountOut = ""
            outPath = ""
            count += 1

            try:


                decoded_transaction = codec.decode.transaction(tx['hash'].hex())
                tx_hash = tx['hash'].hex()
                inputs = decoded_transaction['decoded_input']['inputs']
                # Convert bytes string to hexadecimal format
                for input in inputs:
                    if "PERMIT" in str(input[0]):
                        token = input[1]["struct"]["details"]["token"]
                        amount = input[1]["struct"]["details"]["amount"]
                        permit = "++++"
                    elif "V3_SWAP_EXACT_IN" in str(input[0]):
                        exact_in = "++++"
                        amountIn = input[1]["amountIn"]

                        if type(input[1]["path"]) is not list:
                            inPath = codec.decode.v3_path("V3_SWAP_EXACT_IN", input[1]["path"])
                        else:
                            inPath = input[1]["path"]

                    elif "V3_SWAP_EXACT_OUT" in str(input[0]):
                        exact_out = "++++"
                        amountOut = input[1]["amountOut"]
                        if type(input[1]["path"]) is not list:
                            outPath = codec.decode.v3_path("V3_SWAP_EXACT_OUT", input[1]["path"])
                        else:
                            outPath = input[1]["path"]

                    elif "V2_SWAP_EXACT_IN" in str(input[0]):
                        exact_in = "++++"
                        amountIn = input[1]["amountIn"]
                        inPath = input[1]["path"]

                    elif "V2_SWAP_EXACT_OUT" in str(input[0]):
                        exact_out = "++++"
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

            except:
                print("erroneous transaction")

# Group transactions by token and inPath
from_to_amount = {}
addresses = []

for transaction in transactionList:
    if transaction[4] == "++++":
        lst = ast.literal_eval(transaction[6])

        fr = lst[0]
        to = lst[-1]
        amount = int(transaction[5])
    else:
        lst = ast.literal_eval(transaction[9])

        fr = lst[0]
        to = lst[-1]
        amount = int(transaction[8])

    if fr not in addresses:
        addresses.append(fr)
    if to not in addresses:
        addresses.append(to)

    if (fr, to) not in from_to_amount:
        from_to_amount[(fr, to)] = amount
    else:
        from_to_amount[(fr, to)] += amount

from_to_amount = sorted(from_to_amount.items(), key=lambda x: x[1], reverse=True)

token_names = []
token_addresses = []
for key in from_to_amount:
    first_addr = key[0][0]
    sec_addr = key[0][1]
    first_name = getTheNameOfAToken(first_addr)
    second_name = getTheNameOfAToken(sec_addr)
    if first_name not in token_names:
        token_names.append(first_name)
        token_addresses.append(first_addr)
    if second_name not in token_names:
        token_names.append(second_name)
        token_addresses.append(sec_addr)

print("Total transactions with input starting with '0x3593564c':", count)

Func = open("output.html", "w")
token_count = len(addresses)
min_count = min(token_count, 20)

# Adding input data to the HTML file
str1 = ('''<!DOCTYPE html>
<html lang="en">
  <head>
    <title>Network</title>
    <script
      type="text/javascript"
      src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"
    ></script>
    <style type="text/css">
      #mynetwork {
        width: 600px;
        height: 400px;
        border: 1px solid lightgray;
      }
    </style>
  </head>
  <body>
  <p id=text></p>
    <div class="slidecontainer">'''
        +
        f'''
  <input type="range" 
        min={min_count} 
        max={token_count} 
        value={min_count} 
        class="slider"
        id="myRange"
      />
  <p> Token Count: <span id="demo"></span></p>
</div>
<div><button onclick="draw1()">Draw 1</button>
  <button onclick="draw2()">Draw 2</button>
  </div>
  <div class="container">
    <div id="mynetwork"></div>
<div id="tableContainer"></div>
  </div>

    <script type="text/javascript"> 
    ''' + ''' 
      const fr_to_amount =[];
      function generateTable() {
      var table = document.createElement("table");

      var headerRow = document.createElement("tr");
      var headers = ["From", "To", "Amount"];
      for (var i = 0; i < headers.length; i++) {
        var th = document.createElement("th");
        th.appendChild(document.createTextNode(headers[i]));
        headerRow.appendChild(th);
      }
      table.appendChild(headerRow);

      for (var i = 0; i < fr_to_amount.length; i++) {
        var row = document.createElement("tr");
        for (var j = 0; j < fr_to_amount[i].length; j++) {
          var cell = document.createElement("td");
          cell.appendChild(document.createTextNode(fr_to_amount[i][j]));
          row.appendChild(cell);
        }
        table.appendChild(row);
      }

        var tableContainer = document.getElementById("tableContainer");
        tableContainer.innerHTML = "";
        tableContainer.appendChild(table);
    }''' + f'''

    var slider = document.getElementById("myRange");
    var output = document.getElementById("demo");
    output.innerHTML = slider.value;
    var transaction_count = {count}
    var text = document.getElementById('text');
    text.innerHTML = " Total number of UNISWAP transactions: " + transaction_count;

    var nodes = new vis.DataSet([]);
    var newnodes = [];
    var tokens = [];
    var addresses = [];
    var a = "''' + str(token_names) + '''";
    var b = "''' + str(token_addresses) + '''";
    a = a.replace(/'/g, '"');
    b = b.replace(/'/g, '"');
    tokens = tokens.concat(JSON.parse(a));
    addresses = addresses.concat(JSON.parse(b));

    slider.oninput = function() { 
      output.innerHTML = this.value;
      nodes.clear();
      newnodes=[];
      for (let i = 0; i < slider.value; i++) { 
           newnodes.push({id: i, label: tokens[i], title: addresses[i]});
      }
      nodes.add(newnodes);
    }

    for (let i = 0; i < slider.value; i++) { 
         newnodes.push({id: i, label: tokens[i], title: addresses[i]});
    }
     ''')

s = ""
id = 1

s = s + '''
nodes.add(newnodes);

      '''

for x in from_to_amount:
    s = s + 'fr_to_amount.push(["' + str(getTheNameOfAToken(x[0][0])) + '","' + str(
        getTheNameOfAToken(x[0][1])) + '","' + str(round(x[1] / 1000000000000000000, 2)) + '"]);' + '\n'

s = s + "\n" + "var edges = new vis.DataSet([" + "\n"

cnt = 5

for x in from_to_amount:
    s = s + '{ from: ' + str(token_names.index(getTheNameOfAToken(x[0][0]))) + ' ,to: ' + str(
        token_names.index(getTheNameOfAToken(x[0][1]))) + ', arrows: "to", label: "' + str(
        round(x[1] / 1000000000000000000, 2)) + '", value: ' + str(cnt) + ' },' + '\n'
    cnt = max(cnt - 1, 0)

s = s + ' ]);' + '\n' + '''
      // create a network
      console.log(fr_to_amount);
      var container = document.getElementById("mynetwork");
      var data = {
        nodes: nodes,
        edges: edges,
      };
      var options = {
      layout: {
                      hierarchical: {
                       enabled:false,
                      }
                },
          edges: {
                color: {
                    color: '#EA738D',
                    highlight: '#a973ec',
                }
          },
          nodes: {
                color: {
                    background: '#89ABE3',
                    border: '#89ABE3',
                    highlight: '#a973ec',
                }
          }
      };

      var options2 = {
          layout: {
                      hierarchical: {
                        direction: "LR",
                        sortMethod: "directed"
                      }
                },
          edges: {
                color: {
                    color: '#EA738D',
                    highlight: '#a973ec',
                }
          },
          nodes: {
                color: {
                    background: '#89ABE3',
                    border: '#89ABE3',
                    highlight: '#a973ec',
                }
          }
      };
      generateTable();
      var network = new vis.Network(container, data, options);
      function draw1() {
      network.setOptions(options);
    }
     function draw2() {
      network.setOptions(options2);
    }


    </script>

  </body>
</html>
<style type="text/css">
    table, th, td {
      border:1px solid #ddd;
      font-family: Arial, Helvetica, sans-serif;
      border-collapse: collapse;
      padding: 8px;
    }
    th{
    background-color: #EA738D;
    }
  body {
    margin: 0;
    padding: 0;
  }

  #mynetwork {
    width: 50%;
    height: 100%;
    border: 1px;
  }
  #tableContainer{
  margin-left:100px;
  }
   button
   {
    margin: 5px;
    }
    p{
    padding: 5px;
    }

  .slidecontainer {
  width: 100%;
}

.slider {
  -webkit-appearance: none;
  width: 100%;
  height: 15px;
  border-radius: 5px;
  background: #d3d3d3;
  outline: none;
  opacity: 0.7;
  -webkit-transition: .2s;
  transition: opacity .2s;
}

.slider:hover {
  opacity: 1;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 25px;
  height: 25px;
  border-radius: 50%;
  background: #89ABE3;
  cursor: pointer;
}

.slider::-moz-range-thumb {
  width: 25px;
  height: 25px;
  border-radius: 50%;
  background: #04AA6D;
  cursor: pointer;
}

.container{
display:flex;
}

</style>

'''

output = str1 + s

Func.write(output)

filename = 'file:///' + os.getcwd() + '/' + 'output.html'
webbrowser.open_new_tab(filename)
et = time.time()
elapsed_time = et - st
print('Execution time:', elapsed_time, 'seconds')


def getTheNameOfAToken(address):
    web3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/eth'))

    abi = [{"inputs": [], "name": "name", "outputs": [{"internalType": "string", "name": "", "type": "string"}],
            "stateMutability": "view", "type": "function"},
           {"inputs": [], "name": "symbol", "outputs": [{"internalType": "string", "name": "", "type": "string"}],
            "stateMutability": "view", "type": "function"}]

    contract = web3.eth.contract(address, abi=abi)

    token_name = contract.functions.name().call()

    token_name = token_name.replace("'", "")
    token_name = token_name.replace('"', "")
    return token_name

