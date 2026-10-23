# Raspberry Pi 3 / 4 / 5 keyboard bridge

This replaces the Pico's **USB keyboard entry** only. The Windows PC remains
the app host; the Switch runs SmileBASIC and the original GPU homebrews. The
Pi connects to the Windows host on TCP 39381 over your LAN. In USB gadget
mode it presents a boot-compatible HID keyboard to the Switch; for boards
without a device-capable USB port, manual entry is available. Nothing in
`apps/` changes.

## Hardware and OS

- Raspberry Pi 3, 4 or 5 running Raspberry Pi OS (Python 3, `dwc2`,
  `libcomposite` and `usb_f_hid` for gadget mode).
- For gadget-capable models, a **USB data** connection from the Pi's *device*
  port to the Switch. Pi 4 B and Pi 5 use their USB-C port; provide adequate
  power without back-feeding the Switch (the Switch alone may not supply
  enough). Pi 3 A+ has a USB-A OTG port: use only a suitable device-mode
  connection. Compute Modules depend on the carrier board's USB routing.
- The Pi, Windows host and Switch must share a reachable network. Windows
  needs incoming TCP 39380 (console) and 39381 (keyboard bridge).

| Selection | USB HID keyboard | Connection |
| --- | --- | --- |
| `--model 3`: Pi 3 A+ or CM3/CM3+ with USB device routed | If `/sys/class/udc` contains one controller | Device-mode port/carrier |
| `--model 3`: Pi 3 B/B+ | **No**: their USB ports are host-only | `--manual` + a keyboard connected to the Switch |
| `--model 4`: Pi 4 B or CM4 with USB device routed | If `/sys/class/udc` contains one controller | USB-C/device port/carrier |
| `--model 5`: Pi 5 or CM5 with USB device routed | If `/sys/class/udc` contains one controller | USB-C/device port/carrier |

For gadget mode, add `dtoverlay=dwc2,dr_mode=peripheral` to the Pi's
`/boot/firmware/config.txt`, reboot, then check `ls /sys/class/udc`. The
launcher checks the actual board against `--model` and refuses HID mode if
there is no controller. A Pi 3 B/B+ **cannot replace the Pico as an automatic
USB keyboard without additional USB device hardware**; the manual path still
uses the Pi for the authenticated session command, but requires input on the
Switch. Other Pi variants lacking routed USB device support can use `--manual`.

## Pair and transfer (Windows PowerShell, from HBLauncher)

Install Node.js 22+, Python 3 + Pillow and `spirv-val.exe` on the Windows
host (the Vulkan SDK provides `spirv-val.exe`; set `SPIRV_VAL` to its full
path if necessary). `node scripts/doctor.cjs --host-only` checks dependencies.
Substitute your Pi's SSH address and Windows PC's LAN IPv4 address below:

```powershell
node smilebasic/pi-keyboard/pair.cjs
ssh pi@raspberrypi.local "mkdir -p ~/hb-pi"
scp -r smilebasic/pi-keyboard smilebasic/bootstrap.bas pi@raspberrypi.local:~/hb-pi/
scp smilebasic/pico-keyboard/secret pi@raspberrypi.local:~/hb-pi/secret
```

On the Pi, restrict the copy of the pairing key and configure the USB keyboard:

```sh
chmod 600 ~/hb-pi/secret
sudo bash ~/hb-pi/pi-keyboard/gadget.sh --model 5
ls -l /dev/hidg0
```

Replace **5** with **4** or **3** for your board. If `/sys/class/udc` is
empty, solve USB gadget mode first or use the manual mode below. The script
must report `USB keyboard ready`; otherwise the Pi cannot type on the Switch.

## First-time bootstrap

Open an **empty EDIT0 editor** on the Switch, set the console's USB keyboard
language to **English (US)**, and connect the configured USB keyboard gadget.
Run on the Pi:

```sh
sudo python3 ~/hb-pi/pi-keyboard/keyboard.py --model 5 --host 192.168.1.10 --secret ~/hb-pi/secret --bootstrap
```

Typing begins after 15 seconds; do not change focus. When it finishes, save
slot 0 as **NS2**. This long step is only needed once. The bootstrap source
is identical to the Pico release.

## Every session

1. Restart SmileBASIC (fresh application process) and focus **Direct mode**.
2. On Windows run `node start.cjs 192.168.1.10`. Wait for `Graphics listener
   ready`. The shared pairing key is checked by `node scripts/doctor.cjs`.
3. On the Pi run:

   ```sh
   sudo python3 ~/hb-pi/pi-keyboard/keyboard.py --model 5 --host 192.168.1.10 --secret ~/hb-pi/secret
   ```

   Leave Direct mode focused for the 15-second delay and automated
   LOAD/RUN/REMOVE/START sequence. The `Out of memory` response to `REMOVE`
   is expected. Keep the Windows host running while playing homebrews.

Replace **5** with **3** or **4** for your board. On Pi 3 B/B+ (or without
an available USB device controller), enter `bootstrap.bas` once manually in
SmileBASIC EDIT0, save as NS2, and connect a regular keyboard to the Switch.
For each new session, run on the Pi:

```sh
python3 ~/hb-pi/pi-keyboard/keyboard.py --model 3 --manual --host 192.168.1.10 --secret ~/hb-pi/secret
```

The Pi displays each fresh host command and waits for your confirmation
after you have typed it in Switch Direct mode. Follow the printed order.
`--manual` does **not** turn the Pi 3 B/B+ into a USB keyboard; it only
replaces the Pico's authenticated host-command exchange.

Never repeat `REMOVE` in the same SmileBASIC process. Restart SmileBASIC after
a failed attempt. For a new Windows/Pi pair, run `pair.cjs` on Windows and copy
its `secret` to the Pi again. Do not publish either copy of the key.

The same host port 39381 and protocol are shared with the existing Pico bridge.
On real hardware verify the gadget enumerates as a USB keyboard on the Switch
before starting a native session; USB/console integration cannot be tested
on a Windows-only development machine.
