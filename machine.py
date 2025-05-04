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