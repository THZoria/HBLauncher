#!/usr/bin/env bash
# Configure a boot-compatible USB HID keyboard through Linux configfs.
set -euo pipefail
model=${2:-}
if [[ ${1:-} != --model || ! $model =~ ^[345]$ || $# != 2 ]]; then
  echo 'Usage: sudo bash gadget.sh --model 3|4|5' >&2
  exit 2
fi
[[ $(id -u) == 0 ]] || { echo 'Run as root on the Raspberry Pi.' >&2; exit 1; }
board=$(tr -d '\0' < /proc/device-tree/model)
case "$model:$board" in
  3:*'Raspberry Pi 3 '*|3:*'Compute Module 3'*|4:*'Raspberry Pi 4 '*|4:*'Raspberry Pi 400'*|4:*'Compute Module 4'*|5:*'Raspberry Pi 5 '*|5:*'Compute Module 5'*) ;;
  *) echo "Selected Pi $model does not match detected board: $board" >&2; exit 1;;
esac
if [[ $board == *'Raspberry Pi 3 Model B'* ]]; then
  echo 'Pi 3 B/B+ USB ports cannot act as a HID device. Use --manual with keyboard.py instead.' >&2
  exit 1
fi
modprobe dwc2
modprobe libcomposite
modprobe usb_f_hid
base=/sys/kernel/config/usb_gadget/ns2_keyboard
[[ -d /sys/kernel/config/usb_gadget ]] || { echo 'USB gadget configfs is unavailable.' >&2; exit 1; }
mapfile -t controllers < <(find /sys/class/udc -mindepth 1 -maxdepth 1 -printf '%f\n')
[[ ${#controllers[@]} -eq 1 ]] || { echo "Expected one USB device controller on Pi $model. Check dtoverlay=dwc2,dr_mode=peripheral, reboot and cable/carrier." >&2; exit 1; }
udc=${controllers[0]}
if [[ -e "$base/UDC" ]]; then
  [[ $(cat "$base/UDC") == "$udc" ]] || { echo 'Keyboard gadget exists but is not bound to this controller; inspect configfs before retrying.' >&2; exit 1; }
  echo 'Keyboard gadget already configured.'
  exit 0
fi
mkdir "$base"
echo 0x1d6b > "$base/idVendor"
echo 0x0104 > "$base/idProduct"
echo 0x0200 > "$base/bcdUSB"
echo 0x0100 > "$base/bcdDevice"
mkdir -p "$base/strings/0x409" "$base/configs/c.1/strings/0x409" "$base/functions/hid.usb0"
echo HBLauncher > "$base/strings/0x409/manufacturer"
echo 'Switch keyboard bridge' > "$base/strings/0x409/product"
echo 'Keyboard' > "$base/configs/c.1/strings/0x409/configuration"
echo 1 > "$base/functions/hid.usb0/protocol"
echo 1 > "$base/functions/hid.usb0/subclass"
echo 8 > "$base/functions/hid.usb0/report_length"
# Standard 8-byte boot keyboard input report and LED output report.
printf '%b' '\x05\x01\x09\x06\xa1\x01\x05\x07\x19\xe0\x29\xe7\x15\x00\x25\x01\x75\x01\x95\x08\x81\x02\x95\x01\x75\x08\x81\x01\x95\x05\x75\x01\x05\x08\x19\x01\x29\x05\x91\x02\x95\x01\x75\x03\x91\x01\x95\x06\x75\x08\x15\x00\x25\x65\x05\x07\x19\x00\x29\x65\x81\x00\xc0' > "$base/functions/hid.usb0/report_desc"
ln -s "$base/functions/hid.usb0" "$base/configs/c.1/hid.usb0"
echo "$udc" > "$base/UDC"
echo "USB keyboard ready on $udc (/dev/hidg0)."
