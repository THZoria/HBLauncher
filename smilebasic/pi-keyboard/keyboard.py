"""Send the Pico keyboard bridge's existing protocol through Linux /dev/hidg0."""
import argparse
import ipaddress
import re
import socket
import time
from pathlib import Path

COMMANDS = [('LOAD "TXT:NS2"', 3), ('', 3), ('RUN', 3),
            ('REMOVE NSR,&H60000000,&H3FFFFFFF', 6)]
START_DELAY = 15
KEY_HOLD = 0.025
KEY_GAP = 0.035
LINE_DELAY = 0.25


def keycode(char):
    """Return USB HID modifier and usage for ASCII on the Switch's US layout."""
    if 'a' <= char <= 'z':
        return 0, ord(char) - ord('a') + 4
    if 'A' <= char <= 'Z':
        return 2, ord(char) - ord('A') + 4
    if '1' <= char <= '9':
        return 0, ord(char) - ord('1') + 30
    if char == '0':
        return 0, 39
    codes = {'\n': (0, 40), ' ': (0, 44), '-': (0, 45), '_': (2, 45),
             '=': (0, 46), '+': (2, 46), '[': (0, 47), ']': (0, 48),
             '\\': (0, 49), '|': (2, 49), ';': (0, 51), ':': (2, 51), "'": (0, 52),
             '"': (2, 52), ',': (0, 54), '<': (2, 54), '.': (0, 55),
             '>': (2, 55), '/': (0, 56), '?': (2, 56),
             '!': (2, 30), '@': (2, 31), '#': (2, 32), '$': (2, 33),
             '%': (2, 34), '^': (2, 35), '&': (2, 36), '*': (2, 37),
             '(': (2, 38), ')': (2, 39)}
    if char not in codes:
        raise ValueError(f'Unsupported US keyboard character: {char!r}')
    return codes[char]


def validate_command(line, host):
    match = re.fullmatch(r'V=START\((\d+(?:,\d+){8})\)', line)
    if not match:
        raise ValueError('Invalid session command from host')
    parts = [int(value) for value in match[1].split(',')]
    if parts[0] != 39380 or parts[1:5] != list(ipaddress.IPv4Address(host).packed) or any(
            value >= 1 << 48 for value in parts[5:]):
        raise ValueError('Session command does not match host or port')


def board_family(board):
    if 'Raspberry Pi 400' in board:
        return '4'
    for family in ('3', '4', '5'):
        if f'Raspberry Pi {family} ' in board or f'Raspberry Pi Compute Module {family}' in board:
            return family
    raise ValueError(f'Unsupported Raspberry Pi board: {board}')


def manual_commands(commands):
    print('Type each line below on the Switch, then press Enter HERE to confirm it completed.')
    for line, _ in commands:
        print(f'On the Switch: {line or "[confirm LOAD dialog if present]"}', flush=True)
        input('Press Enter here after completing this step on the Switch: ')


def type_text(device, text):
    for char in text:
        modifier, usage = keycode(char)
        device.write(bytes((modifier, 0, usage, 0, 0, 0, 0, 0)))
        time.sleep(KEY_HOLD)
        device.write(bytes(8))
        time.sleep(LINE_DELAY if char == '\n' else KEY_GAP)


def main():
    parser = argparse.ArgumentParser(description='Raspberry Pi 3/4/5 keyboard bridge for HBLauncher')
    parser.add_argument('--model', required=True, choices=('3', '4', '5'))
    parser.add_argument('--host', required=True, help='Windows host LAN IPv4')
    parser.add_argument('--secret', required=True, type=Path, help='32-hex-digit shared pairing key file')
    parser.add_argument('--hid', default='/dev/hidg0')
    parser.add_argument('--bootstrap', action='store_true', help='Type bootstrap.bas in an EMPTY EDIT0 editor')
    parser.add_argument('--manual', action='store_true', help='Guide manual typing if no USB device controller exists')
    args = parser.parse_args()
    board = Path('/proc/device-tree/model').read_bytes().decode('ascii').strip('\0')
    if board_family(board) != args.model:
        parser.error(f'--model {args.model} does not match {board}')
    if args.bootstrap and args.manual:
        parser.error('For --manual, enter bootstrap.bas in the Switch editor and save as NS2 first')
    if not args.manual and 'Raspberry Pi 3 Model B' in board:
        parser.error('Pi 3 B/B+ has no USB keyboard gadget port: use --manual')
    ipaddress.IPv4Address(args.host)
    key = args.secret.read_text().strip().lower()
    if not re.fullmatch('[0-9a-f]{32}', key):
        raise ValueError('Pairing key must contain 32 hex digits')
    connection = None
    if args.bootstrap:
        commands = [(Path(__file__).resolve().parents[1] / 'bootstrap.bas').read_text(), 0]
    else:
        connection = socket.create_connection((args.host, 39381), timeout=10)
        connection.sendall(f'NS2KEY1 {key}\n'.encode('ascii'))
        line = connection.makefile('rb').readline(193)
        if not line.endswith(b'\n') or len(line) > 192:
            raise ValueError('Incomplete or oversized host command')
        command = line.rstrip(b'\r\n').decode('ascii')
        validate_command(command, args.host)
        commands = COMMANDS + [(command, 0)]
        connection.sendall(b'READY\n')
    if not args.manual:
        for text, _ in commands:
            for char in text:
                keycode(char)
    if args.manual:
        try:
            connection.sendall(b'TYPING\n')
            manual_commands(commands)
            connection.sendall(b'DONE\n')
        finally:
            connection.close()
        return
    print('Focus EMPTY EDIT0' if args.bootstrap else 'Focus fresh SmileBASIC Direct mode')
    print(f'Typing begins in {START_DELAY}s. Do not change focus.')
    try:
        with open(args.hid, 'wb', buffering=0) as device:
            time.sleep(START_DELAY)
            if connection:
                connection.sendall(b'TYPING\n')
            try:
                for text, pause in commands:
                    type_text(device, text + ('' if args.bootstrap else '\n'))
                    if pause:
                        time.sleep(pause)
                if connection:
                    connection.sendall(b'DONE\n')
            finally:
                device.write(bytes(8))
    finally:
        if connection:
            connection.close()
    print('Done. Save as NS2.' if args.bootstrap else 'Launch commands sent.')


if __name__ == '__main__':
    main()
