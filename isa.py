from __future__ import annotations

from collections import namedtuple
from enum import Enum

# Константы для магических чисел
MAX_ARG_VALUE = 0xFFFFFFFF
MAX_ARG_BYTES = 4


class Opcode(str, Enum):
    DROP = "drop"  # Удаляет верхний элемент стека
    DUP = "dup"  # Дублирует верхний элемент стека
    SWAP = "swap"  # Меняет местами два верхних элемента стека
    ADD = "+"  # Складывает два верхних элемента стека
    SUB = "-"  # Вычитает верхний элемент из второго
    MUL = "*"  # Умножает два верхних элемента
    DIV = "/"  # Делит второй элемент на верхний
    MOD = "%"  # Остаток от деления второго элемента на верхний
    NEGATE = "negate"  # Инвертирует знак верхнего элемента
    EQUAL = "="  # Проверка на равенство
    LESS = "<"  # Проверка: второй < верхнего
    GREATER = ">"  # Проверка: второй > верхнего
    AND = "and"  # Побитовая операция И
    OR = "or"  # Побитовая операция ИЛИ
    XOR = "xor"  # Побитовая операция исключающее ИЛИ
    INVERT = "invert"  # Побитовое НЕ
    IF = "if"  # Начало условия
    STORE = "!"  # addr value !
    FETCH = "@"  # addr @
    IN = "in"  # Считывание символа с клавиатуры
    HALT = "halt"  # Останов
    LIT = "lit"  # Ввод числа
    OUT = "out"  # Вывод символа с вершины стека
    JUMP = "jump"  # Переход на метку
    CALL = "call"  # Переход на процедуру
    RET = "ret"  # Возвращение из процедуры
    CARRY = "c"  # Загрузить значение Carry-flag в стек
    VARIABLE = "variable"  # Создать переменную
    DEFINE_FUNC = ":"  # Объявление функции

    def __str__(self) -> str:
        return str(self.value)


class Term(namedtuple("Term", "line pos word")):
    """Описание выражения из исходного текста программы."""


opcode_to_binary: dict[Opcode, int] = {
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
    Opcode.IN: 0x13,
    Opcode.HALT: 0x14,
    Opcode.LIT: 0x15,
    Opcode.OUT: 0x16,
    Opcode.JUMP: 0x17,
    Opcode.CALL: 0x18,
    Opcode.RET: 0x19,
    Opcode.CARRY: 0x20,
    Opcode.DROP: 0x21,
}

binary_to_opcode: dict[int, Opcode] = {v: k for k, v in opcode_to_binary.items()}


def to_bytes(code, first_ex_instr):
    """Преобразует машинный код в бинарное представление.

    Бинарное представление инструкций:

    ┌─────────┬─────────────────────────────────────────────────────────────┐
    │ 31...24 │ 23                                                        0 │
    ├─────────┼─────────────────────────────────────────────────────────────┤
    │  опкод  │                      аргумент                               │
    └─────────┴─────────────────────────────────────────────────────────────┘
    """
    binary_bytes = bytearray()
    binary_bytes += bytes(4)
    binary_bytes += first_ex_instr.to_bytes(4, byteorder="big")
    for instr in code:
        # print("instr", instr)
        if "opcode" in instr:
            opcode_bin = opcode_to_binary[instr["opcode"]]
            binary_bytes.append(opcode_bin)
            if "arg" in instr:
                arg = instr.get("arg", 0)
                # print(arg)
                binary_bytes.extend(((arg >> 16) & 0xFF, (arg >> 8) & 0xFF, arg & 0xFF))
                # print(((arg >> 16) & 0xFF, (arg >> 8) & 0xFF, arg & 0xFF))
                # print(binary_bytes)
        elif "arg" in instr and "opcode" not in instr:
            arg = instr.get("arg", 0)
            # print(arg)
            if isinstance(arg, int):
                if not (-(2 ** 31) <= arg <= 2 ** 31 - 1):
                    binary_bytes.extend(
                        (
                            (arg >> 56) & 0xFF,
                            (arg >> 48) & 0xFF,
                            (arg >> 40) & 0xFF,
                            (arg >> 32) & 0xFF,
                        )
                    )
                    binary_bytes.extend(
                        (
                            (arg >> 24) & 0xFF,
                            (arg >> 16) & 0xFF,
                            (arg >> 8) & 0xFF,
                            arg & 0xFF,
                        )
                    )
                else:
                    binary_bytes.extend(
                        (
                            (arg >> 24) & 0xFF,
                            (arg >> 16) & 0xFF,
                            (arg >> 8) & 0xFF,
                            arg & 0xFF,
                        )
                    )
            elif isinstance(arg, str):
                for i in range(len(arg)):
                    binary_bytes += bytes(3)
                    binary_bytes.extend(arg[i].encode("ascii"))
    return bytes(binary_bytes)


def has_arg(opcode) -> bool:
    return opcode in [
        0x15,  # lit
        0x17,  # jump
        0x18,  # call
        0x10,  # if
        0x13,  # in
        0x16,  # out
    ]


def to_hex(code, variables_map):
    addr_to_var = {addr - 4 * len(variables_map): name for name, addr in variables_map.items()}
    # print(code)

    """Преобразует машинный код в текстовый файл c шестнадцатеричным представлением.

    Формат вывода:
    <address> - <HEXCODE> - <mnemonic>
    """
    binary_code = to_bytes(code, 8)

    result = []
    after_halt = False
    # print(binary_code)
    i = 8
    while i < len(binary_code):
        has_argument = has_arg(int(str(binary_code[i]), 10))
        if has_argument & (not after_halt) & i + 4 >= len(binary_code):
            break
        address = i
        if after_halt:
            word = (
                    (binary_code[i] << 24)
                    | (binary_code[i + 1] << 16)
                    | (binary_code[i + 2] << 8)
                    | binary_code[i + 3]
            )
            # print(address)
            if address in addr_to_var:
                mnemonic = addr_to_var[address]
            i += 4
        else:
            mnemonic = binary_to_opcode[binary_code[address]].value
            # print(address, int(binary_code[address]), has_argument, mnemonic)
            if binary_to_opcode[binary_code[address]] == Opcode.HALT:
                after_halt = True
            if has_argument:
                word = (
                        (binary_code[i] << 24)
                        | (binary_code[i + 1] << 16)
                        | (binary_code[i + 2] << 8)
                        | binary_code[i + 3]
                )
                arg = (
                        (binary_code[i + 1] << 16)
                        | (binary_code[i + 2] << 8)
                        | binary_code[i + 3]
                )
                # print(arg)
                i += 4
            else:
                word = binary_code[i]
                i += 1

        # Формируем строку в требуемом формате
        hex_word = f"{word:10X}"  # количество символов в строке
        if has_argument:
            line = f"{hex(address)} - {hex_word} - {mnemonic} ({arg:08X})"
        else:
            line = f"{hex(address)} - {hex_word} - {mnemonic}"
        result.append(line)

    return "\n".join(result)


def make_zeros(num, code):
    for i in range(num):
        code.append("0")


def bin_to_opcode(binary_code):
    # print(binary_code)
    code = []
    i = (
            (binary_code[4] << 24)
            | (binary_code[5] << 16)
            | (binary_code[6] << 8)
            | (binary_code[7])
    )
    # print(i)
    make_zeros(i, code)
    code_len = i
    flag_var = False
    while i < len(binary_code):
        if binary_code[i] == 0x00:
            arg = (
                    (binary_code[i + 1] << 16)
                    | (binary_code[i + 2] << 8)
                    | binary_code[i + 3]
            )
            if not flag_var:
                flag_var = True
            else:
                make_zeros(3, code)
            code.append(arg)

            i += 4
        else:
            opcode = binary_to_opcode[binary_code[i]]
            has_argument = has_arg(int(str(binary_code[i]), 10))
            instr = {"index": i, "opcode": opcode}
            # print(binary_code[i], has_argument)
            if has_argument:
                arg = (
                        (binary_code[i + 1] << 16)
                        | (binary_code[i + 2] << 8)
                        | binary_code[i + 3]
                )
                instr["arg"] = arg
                code.append(instr)
                make_zeros(3, code)
                i += 4
                code_len += 4
            else:
                code.append(instr)
                i += 1
                code_len += 1

    return code, code_len + 1
