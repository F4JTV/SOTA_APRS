#!/usr/bin/python3
import os
import re
import sys
import time
import argparse
from socket import *

import gpxpy.gpx
import wget

CALL_RE = r"^[a-zA-Z0-9-]+$"
SOTAMAP_URL = "https://sotl.as/api/geoexport/associations/"
ASSOS_LIST = """3Y - Bouvet Island
4O - Montenegro 
4X - Israel 
5B - Cyprus 
8P - Barbados
9A - Croatia 
9H - Malta
9M2 - West Malaysia
9M6 - East Malaysia
9V - Singapore
A6 - United Arab Emirates
BV - Taiwan
C3 - Andorra
CE3 - Chile - Metropolitan Region
CT - Portugal
CT3 - Madeira
CU - Azores
CX - Uruguay
DL - Germany (Alpine)
DM - Germany (Low Mountains)
DU2 - Philippines - North Luzon
DU3 - Philippines - Central Luzon
DU4 - Philippines - Bicol
DUC - Philippines - Calabarzon
E5 - Cook Islands
E7 - Bosnia and Herzegovina
EA1 - Spain - North West
EA2 - Spain - North
EA3 - Spain - Catalunya
EA4 - Spain - Central
EA5 - Spain - South East
EA6 - Spain - Balearic Islands
EA7 - Spain - South
EA8 - Spain - Canary Islands
EA9 - Spain - Ceuta
EI - Ireland
ER - Moldova
ES - Estonia
F - France
FG - Guadeloupe
FH - Mayotte
FK - New Caledonia
FL - France - Low
FM - Martinique
FP - St.Pierre & Miquelon
FR - La Réunion
G - England
GD - Isle Of Man
GI - Northern Ireland
GJ - Bailiwick of Jersey
GM - Scotland
GU - Bailiwick of Guernsey
GW - Wales
HA - Hungary
HB - Switzerland
HB0 - Liechtenstein
HI - Dominican Republic
HL - South Korea
HR - Honduras
I - Italy
IA - Isole Africane d'Italia
IS0 - Sardinia
JA - Japan - Honshu
JA5 - Japan - Shikoku
JA6 - Japan - Kyushu_Okinawa
JA8 - Japan - Hokaido
JW - Svalbard
JX - Jan Mayen
K0M - USA - Minnesota
KH0 - USA - Northern Mariana Islands
KH2 - USA - Guam
KH6 - USA - Hawaii
KH8 - American Samoa
KLA - Alaska - Anchorage
KLF - Alaska - Fairbanks
KLS - Alaska - Southeast
KP4 - USA - Puerto Rico
LA - Norway
LUD - Argentina - Buenos Aires
LUH - Argentina - Córdoba
LUI - Argentina - Misiones
LUK - Argentina - Tucumán
LUM - Argentina - Mendoza
LUN - Argentina - Santiago del Estero
LUP - Argentina - San Juan
LUQ - Argentina - San Luis
LUU - Argentina - La Pampa
LUV - Argentina - Rio Negro
LUY - Argentina - Neuquén
LX - Luxembourg
LY - Lithuania
LZ - Bulgaria
OD - Lebanon
OE - Austria
OH - Finland
OK - Czechia
OM - Slovakia
ON - Belgium
OY - Faroes
OZ - Denmark
PA - Netherlands
PP1 - Brazil - Espírito Santo
PP2 - Brazil - Goiás
PP5 - Brazil - Santa Catarina
PP6 - Brazil - Sergipe
PP7 - Brazil - Alagoas
PQ2 - Brazil - Tocantins
PR8 - Brazil - Maranhão
PS7 - Brazil - Rio Grande do Norte
PS8 - Brazil - Piauí
PT2 - Brazil - Federal District
PT7 - Brazil - Ceará
PY1 - Brazil - Rio de Janeiro
PY2 - Brazil - Sao Paulo
PY3 - Brazil - Rio Grande do Sul
PY4 - Brazil - Minas Gerais
PY5 - Brazil - Paraná
PY6 - Brazil - Bahia
PYF - Brazil - Fernando de Noronha
PYT - Brazil - Trindade & Martim Vaz Is.
R3 - Russia (European)
R9U - Russia - Urals
S2 - Bangladesh
S5 - Slovenia
S7 - Seychelles
SM - Sweden
SP - Poland
SV - Greece
TF - Iceland
TI - Costa Rica
TK - Corsica
UT - Ukraine
V5 - Namibia
VE1 - Canada - Nova Scotia
VE2 - Canada - Québec
VE3 - Canada - Ontario
VE4 - Canada - Manitoba
VE5 - Canada - Saskatchewan
VE6 - Canada - Alberta
VE7 - Canada - British Columbia
VE9 - Canada - New Brunswick
VK1 - Australia - Capital Territory
VK2 - Australia - NSW
VK3 - Australia - Victoria
VK4 - Australia - Queensland
VK5 - Australia - South Australia
VK6 - Australia - WA
VK7 - Australia - Tasmania
VK8 - Australia - Northern Territory
VK9 - Australia - Islands
VKH - Heard Island
VKM - Macquarie Island
VO1 - Canada - Newfoundland
VO2 - Canada - Labrador
VP8 - Falkland Islands
VR - Hong Kong
VY1 - Canada - Yukon
VY2 - Canada - PEI
W0C - USA - Colorado
W0D - USA - Dakotas
W0I - USA - Iowa
W0M - USA - Missouri
W0N - USA - Nebraska
W1 - USA
W2 - USA
W3 - USA
W4A - USA - Alabama
W4C - USA - Carolinas
W4G - USA - Georgia
W4K - USA - Kentucky
W4T - USA - Tennessee
W4V - USA - Virginia
W5A - USA - Arkansas
W5M - USA - Mississippi
W5N - USA - New Mexico
W5O - USA - Oklahoma
W5T - USA - Texas
W6 - USA
W7A - USA - Arizona
W7I - USA - Idaho
W7M - USA - Montana
W7N - USA - Nevada
W7O - USA - Oregon
W7U - USA - Utah
W7W - USA - Washington
W7Y - USA - Wyoming
W8M - USA - Michigan
W8O - USA - Ohio
W8V - USA - West Virginia
W9 - USA - W9
XE1 - Mexico - Central
XE2 - Mexico - North
XE3 - Mexico South
XF4 - Revillagigedo
YBB - Indonesia - Bali
YBE - Indonesia - Eastern Islands of Sumatera
YBJ - Indonesia - Java
YBS - Indonesia - Sumatera
YL - Latvia
YO - Romania
YU - Serbia
Z3 - North Macedonia
ZB2 - Gibraltar
ZD - UK South Atlantic
ZL1 - New Zealand - North Island
ZL3 - New Zealand - South Island
ZL7 - Chatham Islands
ZL8 - Kermadec Islands
ZL9 - Sub - Antarctic Territories
ZS - South Africa
ZS8 - Marion and Prince Edward Islands"""

assos_parse = ASSOS_LIST.splitlines()
asso_dict = {}
for asso in assos_parse:
    key, value = asso.split("-", 1)
    asso_dict[key.strip()] = value.strip()


def convert_coords(latitude, longitude):
    lat_degrees = int(abs(latitude))
    lat_minutes = format((abs(latitude) - lat_degrees) * 60, '.2f')

    long_degrees = int(abs(longitude))
    long_minutes = format((abs(longitude) - long_degrees) * 60, '.2f')

    lat_direction = "N" if latitude >= 0 else "S"
    long_direction = "E" if longitude >= 0 else "W"

    lat_degrees_str = str(lat_degrees)
    long_degrees_string = str(long_degrees)

    if lat_degrees_str.startswith("-"):
        lat_degrees_str = lat_degrees_str[1:]
    if long_degrees_string.startswith("-"):
        long_degrees_string = long_degrees_string[1:]

    if len(long_degrees_string) < 3:
        long_degrees_string = "0" + long_degrees_string
    if len(lat_degrees_str) < 2:
        lat_degrees_str = "0" + lat_degrees_str

    converted = (lat_degrees_str + lat_minutes.zfill(5) + lat_direction + "S" +
                 long_degrees_string.zfill(3) + long_minutes.zfill(5) + long_direction)

    return converted


def get_passcode(ham_callsign):
    if re.match(CALL_RE, ham_callsign):
        call = ham_callsign.upper()

        i = 0
        tmp_code = 29666
        while i < len(call):
            try:
                tmp_code = tmp_code ^ ord(call[i]) * 256
                tmp_code = tmp_code ^ ord(call[i + 1])
                i += 2
            except IndexError:
                break

        passc = tmp_code & 32767
        print(f"[+] APRS passcode for {call}: {passc}")

        return passc

    else:
        print("[-] Invalid Callsign")
        sys.exit(1)


parser = argparse.ArgumentParser(prog="SOTA_summit_2_APRS.py",
                                 formatter_class=argparse.RawTextHelpFormatter,
                                 description=ASSOS_LIST,
                                 epilog="In SOTA, we trust")
parser.add_argument("-c", "--callsign", dest="callsign", required=True, type=str, help="HAM callsign")
group = parser.add_mutually_exclusive_group()
group.add_argument("-g", "--gpx", dest="gpx_file", type=str, help="sotamaps.org .gpx file", action="extend", nargs="*")
group.add_argument("-a", "--asso", dest="asso", type=str, help="SOTA association prefix", action="extend", nargs="*")
args = parser.parse_args()

callsign = args.callsign.upper()
passcode = get_passcode(callsign)
gpx_summit_file = ""
asso = ""
gpx_summit_file_list = []

if args.gpx_file:
    gpx_summit_file = args.gpx_file
    for file_name in gpx_summit_file:
        gpx_summit_file_list.append(file_name)

elif args.asso:
    asso = args.asso
    for prefix in asso:
        if prefix in asso_dict.keys():
            print(f"Downloading {prefix}.gpx from sotl.as")
            wget.download(f"{SOTAMAP_URL + prefix + '.gpx'}")
            print("\nDone")
            gpx_summit_file_list.append(f"{prefix + '.gpx'}")
        else:
            print(f"Omitted {prefix}: not in the official association list")

for file in gpx_summit_file_list:
    try:
        with open(file, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)

            for waypoint in gpx.waypoints:
                summit_name = waypoint.comment
                summit_ref = waypoint.name
                while len(summit_ref) < 9:
                    summit_ref = " " + summit_ref
                summit_coords = convert_coords(waypoint.latitude, waypoint.longitude)
                summit_elevation = int(waypoint.elevation)

                try:
                    sock = socket(AF_INET, SOCK_STREAM)
                    sock.connect(("euro.aprs2.net", 14580))
                    connect_packet = f'user {callsign} pass {passcode} vers "SOTA Summit APRS" filter r/0/0/1\n'
                    sock.send(bytes(connect_packet, 'utf-8'))
                    print(sock.recv(1000).decode("utf-8"))
                    packet = (f"{callsign}-10>APDG03,TCPIP*,qAC,{callsign}:;{summit_ref}"
                              f"*111111z{summit_coords};{summit_name} "
                              f"{summit_elevation}m, https://sotl.as/summits/{summit_ref.strip()}")
                    sock.send(bytes(packet + " \n", 'utf-8'))
                    print(sock.recv(1000).decode("utf-8"))
                    sock.shutdown(0)
                    sock.close()
                    print(packet)

                except Exception as e:
                    print(e)

                time.sleep(0.1)

    except gpxpy.gpx.GPXXMLSyntaxException:
        print("[-] Bad .gpx file\n[-] Please put a valid .gpx file from -> https://www.sotamaps.org/")
        sys.exit(2)
    except KeyboardInterrupt:
        print("[-] Script stopped by user")
        sys.exit(3)
    except FileNotFoundError:
        print("[-] Please select a valid .gpx file name")
        sys.exit(4)

    os.remove(file)
