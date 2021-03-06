import argparse
from subprocess import check_output
import re
from json import dumps
from datetime import datetime

parser = argparse.ArgumentParser('Calls nmap with given arguments \
                                    and pushes the result to a database')

parser.add_argument('--search-address',
                    type=str,
                    help='IP address to search with nmap',
                    required=True)
parser.add_argument('--nmap-option',
                    type=str,
                    help='Option to use with nmap')
parser.add_argument('--search-mask',
                    type=int,
                    help='Subnet mask used to specify a subnet to search')
args = parser.parse_args()

# Generate nmap command
nmap_str = 'nmap'

if args.nmap_option is not None:
    nmap_str += ' -' + args.nmap_option

nmap_str += ' ' + args.search_address

if args.search_mask is not None:
    nmap_str += '/' + str(args.search_mask)

# Call nmap, retrieve raw result
result = check_output(nmap_str, shell=True)
res_iter = iter(result.split('\n'))

# Parse result
hosts = []

while True:
    try:
        line = next(res_iter)

        if re.match('Nmap\sscan\sreport\sfor', line) is not None:
            host_data = {}
            host_data['open_ports'] = []
            host_data['timestamp'] = datetime.now().isoformat()

            raw_data = line.split()
            if len(raw_data) == 5:
                host_data['ip'] = raw_data[4]
            elif len(raw_data) == 6:
                host_data['name'] = raw_data[4]
                host_data['ip'] = raw_data[5].replace('(', '').replace(')', '')
            else:
                continue

            while line.strip():
                line = next(res_iter)
                # Match port list header
                if re.match('PORT\s+STATE', line):
                    # Look up each open port
                    while True:
                        line = next(res_iter)
                        port_match = re.match('(\d+)/(\w+)\s+(?:(open)|)', line)
                        if port_match is not None:
                            # Only parse open ports
                            if port_match.group(3) is not None:
                                port = int(port_match.group(1))
                                host_data['open_ports'].append(port)
                        else:
                            break
                # Match MAC address
                mac_match = re.match(r'MAC\sAddress:\s((?:\w\w:){5}\w\w)(\s\((?:\w|\s)+\))?', line)
                if mac_match is not None:
                    host_data['mac'] = mac_match.group(1)
                    if mac_match.group(2) is not None and mac_match.group(2) != '(Unknown)':
                        host_data['mac_provider'] = mac_match.group(2).replace('(', '').replace(')', '')

            hosts.append(host_data)
    except StopIteration:
        break

print(dumps(hosts))
