#!/usr/bin/python3
import re
import sys
import time
import argparse
from socket import *

import gpxpy.gpx

CALL_RE = r"^[a-zA-Z0-9-]+$"
# "https://www.sotamaps.org/index_tools.php?what=creategpxfile&asncode=F&rgncode=AM&sortmode=code"


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


parser = argparse.ArgumentParser()
parser.add_argument("-c", "--callsign", dest="callsign", required=True, type=str, help="HAM callsign")
parser.add_argument("-g", "--gpx", dest="gpx_file", required=True, type=str, help="sotamaps.org .gpx file")
args = parser.parse_args()

callsign = args.callsign.upper()
passcode = get_passcode(callsign)
gpx_summit_file = args.gpx_file

try:
    with open(gpx_summit_file, 'r') as gpx_file:
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

            time.sleep(1)

except gpxpy.gpx.GPXXMLSyntaxException:
    print("[-] Bad .gpx file\n[-] Please put a valid .gpx file from -> https://www.sotamaps.org/")
    sys.exit(2)
except KeyboardInterrupt:
    print("[-] Script stopped by user")
    sys.exit(3)
except FileNotFoundError:
    print("[-] Please select a valid .gpx file name")
    sys.exit(4)
