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
    LIT = "lit"  # Ввод числа
    EMIT = "emit"  # Вывод символа с вершины стека
    JUMP = "jump"  # Переход на метку
    CALL = "call"  # Переход на процедуру
    RET = "ret"  # Возвращение из процедуры
    CARRY = "c"  # Загрузить значение Overflow-flag в стек

    def __str__(self):
        return str(self.value)


class Term(namedtuple("Term", "line pos symbol")):
    """Описание выражения из исходного текста программы.

        Сделано через класс, чтобы был docstring.
        """


# Словарь соответствия кодов операций их бинарному представлению
opcode_to_binary = {
    Opcode.DROP: 0x00,
    Opcode.DUP: 0x01,
    Opcode.SWAP: 0x02,
    Opcode.ADD: 0x03,
    Opcode.SUB: 0x04,
    Opcode.MUL: 0x05,
    Opcode.DIV: 0x06,
    Opcode.MOD: 0x07,
    Opcode.NEGATE: 0x08,
    Opcode.EQUAL: 0x09,
    Opcode.LESS: 0x0A,
    Opcode.GREATER: 0x0B,
    Opcode.AND: 0x0C,
    Opcode.OR: 0x0D,
    Opcode.XOR: 0x0E,
    Opcode.INVERT: 0x0F,
    Opcode.IF: 0x10,
    Opcode.STORE: 0x11,
    Opcode.FETCH: 0x12,
    Opcode.KEY: 0x13,
    Opcode.HALT: 0x14,
    Opcode.LIT: 0x15,
    Opcode.EMIT: 0x16,
    Opcode.JUMP: 0x17,
    Opcode.CALL: 0x18,
    Opcode.RET: 0x19,
    Opcode.CARRY: 0x20,
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
    0x11: Opcode.STORE,
    0x12: Opcode.FETCH,
    0x13: Opcode.KEY,
    0x14: Opcode.HALT,
    0x15: Opcode.LIT,
    0x16: Opcode.EMIT,
    0x17: Opcode.JUMP,
    0x18: Opcode.CALL,
    0x19: Opcode.RET,
    0x20: Opcode.CARRY,
}


def to_bytes(code):
    binary_bytes = bytearray()
    for instr in code:
        opcode_val = opcode_to_binary[instr["opcode"]] & 0xFF
        binary_bytes.append(opcode_val)

        if instr["opcode"] in (Opcode.IF, Opcode.LIT, Opcode.JUMP, Opcode.CALL, Opcode.KEY, Opcode.EMIT):
            arg = instr.get("arg", 0)

            if not (0 <= arg <= 0xFFFFFFFF):
                raise ValueError(f"Аргумент {arg} превышает допустимые 32 бита")

            arg_bytes = []
            temp = arg
            while temp > 0:
                arg_bytes.insert(0, temp & 0xFF)
                temp >>= 8

            if len(arg_bytes) > 4:
                raise ValueError(f"Аргумент {arg} требует более 4 байт")

            binary_bytes.extend(arg_bytes)
    return bytes(binary_bytes)


def to_hex(code):
    result = []
    i = 0
    addr = 0
    iter = 0

    for instr in code:
        opcode_val = opcode_to_binary[instr["opcode"]] & 0xFF
        hex_parts = [f"{opcode_val:02X}"]
        i += 1

        arg_str = ""
        if instr["opcode"] in (Opcode.IF, Opcode.LIT, Opcode.JUMP, Opcode.CALL, Opcode.KEY, Opcode.EMIT):
            arg = instr.get("arg", 0)
            arg_bytes = []
            temp = arg
            while temp > 0:
                arg_bytes.insert(0, temp & 0xFF)
                temp >>= 8
            if not arg_bytes:
                arg_bytes = [0]

            hex_parts.extend(f"{b:02X}" for b in arg_bytes)
            i += len(arg_bytes)
            arg_str = f" {arg}"

        hex_word = ''.join(hex_parts)
        mnemonic = instr["opcode"].value
        result.append(f"{iter} - {hex_word} - {mnemonic}{arg_str}")
        addr = i
        iter += 1

    return "\n".join(result)


def from_bytes(binary_code):
    structured_code = []
    for line in binary_code.strip().splitlines():
        parts = line.strip().split(" - ")
        if len(parts) < 3:
            continue

        index_str, hex_word, mnemonic = parts
        index = int(index_str)
        word_bytes = bytes.fromhex(hex_word)

        if len(word_bytes) == 0:
            raise ValueError(f"Пустая строка байтов в строке: {line}")

        opcode_val = word_bytes[0]
        opcode = binary_to_opcode.get(opcode_val)

        if opcode is None:
            raise ValueError(f"Неизвестный бинарный код операции: {opcode_val:#X} в строке: {line}")

        instr = {"index": index, "opcode": opcode}

        if opcode in (Opcode.IF, Opcode.LIT, Opcode.JUMP, Opcode.CALL, Opcode.KEY, Opcode.EMIT):
            arg_bytes = word_bytes[1:]
            if not arg_bytes:
                raise ValueError(f"Инструкция {opcode} требует аргумент, но он отсутствует в строке: {line}")

            arg = 0
            for b in arg_bytes:
                arg = (arg << 8) | b
            instr["arg"] = arg

        structured_code.append(instr)
    return structured_code


def write_json(filename, code):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(code, file, indent=4)
