import importlib.util
import io
import pathlib
import unittest
from unittest.mock import patch

source = pathlib.Path(__file__).with_name('keyboard.py')
spec = importlib.util.spec_from_file_location('pi_keyboard', source)
keyboard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(keyboard)


class KeyboardTests(unittest.TestCase):
    def test_bootstrap_and_session_commands_are_typeable(self):
        source_text = source.parents[1].joinpath('bootstrap.bas').read_text()
        for char in source_text + ''.join(line for line, _ in keyboard.COMMANDS):
            keyboard.keycode(char)
        keyboard.validate_command('V=START(39380,192,168,1,10,1,2,3,4)', '192.168.1.10')

    def test_wrong_host_and_malformed_command_are_rejected(self):
        for command in ('V=START(39380,192,168,1,11,1,2,3,4)',
                        'V=START(39381,192,168,1,10,1,2,3,4)',
                        'V=START(39380,192,168,1,10,1,2,3,281474976710656)',
                        'V=START(39380,192,168,1,10,1,2,3,4):RUN'):
            with self.assertRaises(ValueError):
                keyboard.validate_command(command, '192.168.1.10')

    def test_model_selection_and_manual_fallback(self):
        for board, family in [('Raspberry Pi 3 Model A+ Rev 1.0', '3'),
                              ('Raspberry Pi 3 Model B Plus Rev 1.3', '3'),
                              ('Raspberry Pi 4 Model B Rev 1.2', '4'),
                              ('Raspberry Pi Compute Module 4 Rev 1.0', '4'),
                              ('Raspberry Pi 5 Model B Rev 1.0', '5')]:
            self.assertEqual(keyboard.board_family(board), family)
        with self.assertRaises(ValueError):
            keyboard.board_family('Raspberry Pi Zero 2 W')
        with patch('builtins.input', return_value='') as confirm:
            with patch('builtins.print'):
                keyboard.manual_commands(keyboard.COMMANDS)
            self.assertEqual(confirm.call_count, len(keyboard.COMMANDS))

    def test_hid_packet_is_released_between_keystrokes(self):
        device = io.BytesIO()
        with patch.object(keyboard.time, 'sleep'):
            keyboard.type_text(device, 'A\n')
        self.assertEqual(device.getvalue(), bytes((2, 0, 4, 0, 0, 0, 0, 0)) + bytes(8)
                         + bytes((0, 0, 40, 0, 0, 0, 0, 0)) + bytes(8))


if __name__ == '__main__':
    unittest.main()
