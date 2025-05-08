"""Представление исходного и машинного кода.

Определено два представления:
- Бинарное
- JSON
"""

import json
from collections import namedtuple
from enum import Enum


class Opcode(str, Enum):
    DROP = "drop"  # Удаляет верхний элемент стека
    DUP = "dup"  # Дублирует верхний элемент стека
    SWAP = "swap"  # Меняет местами два верхних элемента стека
    ADD = "+"  # Складывает два верхних элемента стека
    SUB = "-"  # Вычитает верхний элемент из второго
    MUL = "*"  # Умножает два верхних элемента
    DIV = "/"  # Делит второй элемент на верхний
    MOD = "mod"  # Остаток от деления второго элемента на верхний
    NEGATE = "negate"  # Инвертирует знак верхнего элемента
    EQUAL = "="  # Проверка на равенство
    LESS = "<"  # Проверка: второй < верхнего
    GREATER = ">"  # Проверка: второй > верхнего
    AND = "and"  # Побитовая операция И
    OR = "or"  # Побитовая операция ИЛИ
    XOR = "xor"  # Побитовая операция исключающее ИЛИ
    INVERT = "invert"  # Побитовое НЕ
    IF = "if"  # Начало условия
    EXIT = "exit"  # Завершение выполнения слова
    STORE = "!"  # addr value !
    FETCH = "@"  # addr @
    KEY = "key"  # Считывание символа с клавиатуры
    HALT = "halt"  # Останов
    LIT = "lit" # Ввод числа
    EMIT = "emit" # Вывод символа с вершины стека
    JUMP = "jump"



    def __str__(self):
        return str(self.value)


class Term(namedtuple("Term", "line pos symbol")):
    """Описание выражения из исходного текста программы.

        Сделано через класс, чтобы был docstring.
        """


# Словарь соответствия кодов операций их бинарному представлению
opcode_to_binary = {
    Opcode.DROP:     0x00,
    Opcode.DUP:      0x01,
    Opcode.SWAP:     0x02,
    Opcode.ADD:      0x03,
    Opcode.SUB:      0x04,
    Opcode.MUL:      0x05,
    Opcode.DIV:      0x06,
    Opcode.MOD:      0x07,
    Opcode.NEGATE:   0x08,
    Opcode.EQUAL:    0x09,
    Opcode.LESS:     0x0A,
    Opcode.GREATER:  0x0B,
    Opcode.AND:      0x0C,
    Opcode.OR:       0x0D,
    Opcode.XOR:      0x0E,
    Opcode.INVERT:   0x0F,
    Opcode.IF:       0x10,
    Opcode.EXIT:     0x11,
    Opcode.STORE:    0x12,
    Opcode.FETCH:    0x13,
    Opcode.KEY:      0x14,
    Opcode.HALT:     0x15,
    Opcode.LIT:      0x16,
    Opcode.EMIT:     0x17,
    Opcode.JUMP:     0x18,
}

# Словарь соответствия бинарных значений к операциям
binary_to_opcode = {
    0x00: Opcode.DROP,
    0x01: Opcode.DUP,
    0x02: Opcode.SWAP,
    0x03: Opcode.ADD,
    0x04: Opcode.SUB,
    0x05: Opcode.MUL,
    0x06: Opcode.DIV,
    0x07: Opcode.MOD,
    0x08: Opcode.NEGATE,
    0x09: Opcode.EQUAL,
    0x0A: Opcode.LESS,
    0x0B: Opcode.GREATER,
    0x0C: Opcode.AND,
    0x0D: Opcode.OR,
    0x0E: Opcode.XOR,
    0x0F: Opcode.INVERT,
    0x10: Opcode.IF,
    0x11: Opcode.EXIT,
    0x12: Opcode.STORE,
    0x13: Opcode.FETCH,
    0x14: Opcode.KEY,
    0x15: Opcode.HALT,
    0x16: Opcode.LIT,
    0x17: Opcode.EMIT,
    0x18: Opcode.JUMP,
}

def to_bytes(code):
    binary_bytes = bytearray()
    for instr in code:
        opcode_val = opcode_to_binary[instr["opcode"]] & 0xFF  # 8 бит на опкод
        arg = instr.get("arg", 0) & 0x00FFFFFF  # 24 бита на аргумент
        binary_instr = (opcode_val << 24) | arg
        binary_bytes.extend([
            (binary_instr >> 24) & 0xFF,
            (binary_instr >> 16) & 0xFF,
            (binary_instr >> 8) & 0xFF,
            binary_instr & 0xFF
        ])
    return bytes(binary_bytes)



def to_hex(code):
    binary_code = to_bytes(code)
    result = []
    for i in range(0, len(binary_code), 4):
        if i + 3 >= len(binary_code):
            break

        word = (binary_code[i] << 24) | (binary_code[i + 1] << 16) | (binary_code[i + 2] << 8) | binary_code[i + 3]
        opcode_bin = (word >> 24) & 0xFF
        arg = word & 0x00FFFFFF

        opcode = binary_to_opcode.get(opcode_bin)
        if opcode is None:
            mnemonic = f"UNKNOWN_{opcode_bin:02X}"
        else:
            mnemonic = opcode.value
            if opcode in (Opcode.IF, Opcode.LIT, Opcode.JUMP):
                mnemonic += f" {arg}"

        hex_word = f"{word:08X}"
        address = i // 4
        line = f"{address} - {hex_word} - {mnemonic}"
        result.append(line)
    return "\n".join(result)



def from_bytes(binary_code):
    structured_code = []
    for line in binary_code.strip().splitlines():
        parts = line.strip().split(" - ")
        if len(parts) < 3:
            continue
        index_str, hex_word, mnemonic = parts
        index = int(index_str)
        word = int(hex_word, 16)
        opcode_bin = (word >> 24) & 0xFF
        arg = word & 0x00FFFFFF
        opcode = binary_to_opcode.get(opcode_bin)
        if opcode is None:
            raise ValueError(f"Неизвестный бинарный код операции: {opcode_bin:#X} в строке: {line}")
        instr = {"index": index, "opcode": opcode}
        if opcode in (Opcode.IF, Opcode.LIT):
            instr["arg"] = arg
        structured_code.append(instr)
    return structured_code



def write_json(filename, code):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(code, file, indent=4)
