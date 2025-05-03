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
    THEN = "then"  # Завершение условия
    EXIT = "exit"  # Завершение выполнения слова
    STORE = "!"  # addr value !
    FETCH = "@"  # addr @
    KEY = "key"  # Считывание символа с клавиатуры

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
    Opcode.THEN:     0x11,
    Opcode.EXIT:     0x12,
    Opcode.STORE:    0x13,
    Opcode.FETCH:    0x14,
    Opcode.KEY:      0x15,
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
    0x11: Opcode.THEN,
    0x12: Opcode.EXIT,
    0x13: Opcode.STORE,
    0x14: Opcode.FETCH,
    0x15: Opcode.KEY,
}

def to_bytes(code):
    binary_bytes = bytearray()
    for instr in code:
        # Получаем бинарный код операции
        opcode_bin = opcode_to_binary[instr["opcode"]] << 28

        # Добавляем адрес перехода, если он есть
        arg = instr.get("arg", 0)

        # Формируем 32-битное слово: опкод (4 бита) + адрес (28 бит)
        binary_instr = opcode_bin | (arg & 0x0FFF_FFFF)

        # Преобразуем 32-битное целое число в 4 байта (big-endian)
        binary_bytes.extend(
            ((binary_instr >> 24) & 0xFF, (binary_instr >> 16) & 0xFF, (binary_instr >> 8) & 0xFF, binary_instr & 0xFF)
        )

    return bytes(binary_bytes)


def to_hex(code):
    """Преобразует машинный код в текстовый файл с шестнадцатеричным представлением.

    Формат вывода:
    <address> - <HEXCODE> - <mnemonic>
    Например:
    20 - 03340301 - add #01 <- 34 + #03
    """
    binary_code = to_bytes(code)
    result = []

    for i in range(0, len(binary_code), 4):
        if i + 3 >= len(binary_code):
            break

        # Формируем 32-битное слово из 4 байтов
        word = (binary_code[i] << 24) | (binary_code[i + 1] << 16) | (binary_code[i + 2] << 8) | binary_code[i + 3]

        # Получаем опкод и адрес
        opcode_bin = (word >> 28) & 0xF
        arg = word & 0x0FFF_FFFF

        # Преобразуем опкод и адрес в мнемонику
        mnemonic = binary_to_opcode[opcode_bin].value
        if opcode_bin in (0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18):
            mnemonic = f"{mnemonic} {arg}"

        # Формируем строку в требуемом формате
        hex_word = f"{word:08X}"
        address = i // 4
        line = f"{address} - {hex_word} - {mnemonic}"
        result.append(line)

    return "\n".join(result)


def from_bytes(binary_code):
    """Преобразует бинарное представление машинного кода в структурированный формат.

    Бинарное представление инструкций:

    ┌─────────┬─────────────────────────────────────────────────────────────┐
    │ 31...28 │ 27                                                        0 │
    ├─────────┼─────────────────────────────────────────────────────────────┤
    │  опкод  │                      адрес перехода                         │
    └─────────┴─────────────────────────────────────────────────────────────┘
    """
    structured_code = []
    # Обрабатываем байты по 4 за раз для получения 32-битных инструкций
    for i in range(0, len(binary_code), 4):
        if i + 3 >= len(binary_code):
            break

        # Формируем 32-битное слово из 4 байтов
        binary_instr = (
                (binary_code[i] << 24) | (binary_code[i + 1] << 16) | (binary_code[i + 2] << 8) | binary_code[i + 3]
        )

        # Извлекаем опкод (старшие 4 бита)
        opcode_bin = (binary_instr >> 28) & 0xF
        opcode = binary_to_opcode[opcode_bin]

        # Извлекаем адрес перехода (младшие 28 бит)
        arg = binary_instr & 0x0FFF_FFFF

        # Формируем структуру инструкции
        instr = {"index": i // 4, "opcode": opcode}

        # Добавляем адрес перехода только для инструкций перехода
        if opcode in {Opcode.IF, Opcode.ELSE, Opcode.THEN, Opcode.BEGIN, Opcode.UNTIL, Opcode.WHILE, Opcode.REPEAT,
                      Opcode.DO, Opcode.LOOP}:
            instr["arg"] = arg

        structured_code.append(instr)

    return structured_code


def write_json(filename, code):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(code, file, indent=4)
