import logging
import sys
from isa import Opcode, from_bytes,opcode_to_binary

class Datapath:
    stack_first = None # Верхняя ячейка стека
    stack_second = None # Нижняя ячейка стека
    input_buffer = None # Буфер входных данных. Инициализируется входными данными конструктора.
    output_buffer = None # Буфер выходных данных.
    data_memory_size = None # Размер памяти данных.
    data_memory = None # Память данных. Инициализируется нулевыми значениями.
    data_address = None # Адрес в памяти данных. Инициализируется нулём.

    def __init__(self, data_memory_size, input_buffer):
        assert data_memory_size > 0, "Data_memory size should be non-zero"
        self.data_memory_size = data_memory_size
        self.data_memory = [0] * data_memory_size
        self.data_address = 0
        self.stack_first = 0
        self.stack_second = 0
        self.input_buffer = input_buffer
        self.output_buffer = []


class ControlUnit:
    program = None # Память команд.
    program_counter = None # Счётчик команд. Инициализируется нулём.
    data_path = None # Блок обработки данных.
    _tick = None # Текущее модельное время процессора (в тактах). Инициализируется нулём.

    def __init__(self, program, data_path):
        self.program = program
        self.program_counter = 0
        self.data_path = data_path
        self._tick = 0
        self.step = 0

    def tick(self):
        """Продвинуть модельное время процессора вперёд на один такт."""
        self._tick += 1

    def get_tick(self):
        return self._tick

    def signal_latch_program_counter(self, sel_next):
        """Защёлкнуть новое значение счётчика команд.

        Если `sel_next` равен `True`, то счётчик будет увеличен на единицу,
        иначе -- будет установлен в значение аргумента текущей инструкции.
        """
        if sel_next:
            self.program_counter += 1
        else:
            instr = self.program[self.program_counter]
            assert "arg" in instr, "internal error"
            self.program_counter = instr["arg"]