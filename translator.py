#!/usr/bin/python3
"""Транслятор AccForth в машинный код."""

import base64
import os
import re
import sys

from isa import Opcode, Term, to_bytes, to_hex


# комментарии разрешены только после #

class Translator:
    variables_map = None  # имя - адрес
    functions_map = None
    variables_queue = None  # переменные будут сохранены в конце кода, после хальта,
    # чтобы гарантированно не мешать коду; имя - значение
    addresses_in_conditions = None  # код, куда нужно вставить аргумент - аргумент

    def __init__(self):
        self.variables_map = {}
        self.functions_map = {}
        self.variables_queue = {}
        self.addresses_in_conditions = {}

    def instructions(self):
        return {
            "drop", "dup", "swap", "+", "-", "*", "/", "mod", "negate", "=", "<", ">", "and", "or", "xor", "invert",
            "if", "!", "@", "in", "halt", "lit", "out", "jump", "call", "ret", "c"
        }

    def math_instructions(self):  # на этапе трансляции они будут развернуты в POP_AC + POP_DR + INSTR
        return {
            "+",
            "-",
            "*",
            "/",
            "%",
            "negate",
            "and",
            "or",
            "xor",
            "invert",
            "=",
            ">",
            "<",
        }

    def instr_without_arg(self):  # без аргумента
        return {
            "@",
            "!",
            "ret",
            "+",
            "-",
            "*",
            "/",
            "%",
            "negate",
            "and",
            "or",
            "xor",
            "invert",
            "=",
            ">",
            "<",
            "dup",
            "drop",
            "swap",
            "c",
            "halt",
        }

    def second_type_instructions(self):  # с аргументом + LOAD_IMM + CALL
        return {"jump", "call", "if", "in", "out", "lit"}

    def word_to_opcode(self, symbol):
        """Отображение операторов исходного кода в коды операций."""
        return {
            "drop": Opcode.DROP,
            "dup": Opcode.DUP,
            "swap": Opcode.SWAP,
            "+": Opcode.ADD,
            "-": Opcode.SUB,
            "*": Opcode.MUL,
            "/": Opcode.DIV,
            "%": Opcode.MOD,
            "negate": Opcode.NEGATE,
            "=": Opcode.EQUAL,
            "<": Opcode.LESS,
            ">": Opcode.GREATER,
            "and": Opcode.AND,
            "or": Opcode.OR,
            "xor": Opcode.XOR,
            "invert": Opcode.INVERT,
            "if": Opcode.IF,
            "!": Opcode.STORE,
            "@": Opcode.FETCH,
            "in": Opcode.IN,
            "lit": Opcode.LIT,
            "out": Opcode.OUT,
            "jump": Opcode.JUMP,
            "call": Opcode.CALL,
            "ret": Opcode.RET,
            "VARIABLE": Opcode.VARIABLE,
            ":": Opcode.DEFINE_FUNC,
            "halt": Opcode.HALT,
            "c": Opcode.CARRY,
        }.get(symbol)

    def text_to_terms(self, text):
        """Трансляция текста в последовательность операторов языка (токенов).

        Включает в себя:

        - отсеивание всего, что не: команда, имя переменной, имя лейбла, число;
        - проверка формальной корректности программы (if - then; while - repeat)
        """

        terms = []
        for line_num, line in enumerate(text.split("\n")):
            words = line.strip().split()
            for pos, word in enumerate(words, 1):
                if word == ";":
                    break  # если встретили ;, значит это комментарий, значит до конца строки все скипаем

                # слово может быть: командой, числом, лейблом, названием переменной
                # если это число, потом я его распаршу
                terms.append(Term(line_num, pos, word))  # Добавляем токен

        # pos - адрес, потом переименую
        return terms

    def translate_stage_1(self, text):
        """Первый этап трансляции.
        Убираются все токены, которые не отображаются напрямую в команды,
        создается условная таблица линковки для лейблов функций и названий переменных.
        """
        terms = self.text_to_terms(text)

        # Транслируем термы в машинный код.
        code = []
        brackets_stack = []

        i = 0
        address = 8
        hex_number_pattern = r"^0[xX][0-9A-Fa-f]+$"
        dec_number_pattern = r"^[0-9]+$"
        # last_begin = []
        while i < len(terms):
            term = terms[i]
            # print(term)
            if ":" in term.word:
                label = terms[i].word.split(":")[0]
                self.functions_map[label] = address
                address -= 4
            elif self.word_to_opcode(term.word) == Opcode.VARIABLE:
                address -= 4
            elif term.word in self.instr_without_arg():
                address -= 3
            elif self.word_to_opcode(term.word):
                i += 1
                continue
            i += 1
            address += 4
        i = 0
        address = 8
        min_address = min(self.functions_map.values())
        delta = min_address - 8

        for key in self.functions_map:
            self.functions_map[key] -= delta

        # print(self.functions_map)
        while i < len(terms):
            term = terms[i]
            # print(term, address)
            # если это 16 cc число - load_imm
            if re.fullmatch(hex_number_pattern, term.word):

                arg = int(term.word, 16)
                assert -2 ** 63 <= arg <= 2 ** 63 - 1, "Argument is not in range!"
                code.append(
                    {
                        "address": address,
                        "opcode": self.word_to_opcode(terms[i - 1].word),
                        "arg": arg,
                        "term": term,
                    }
                )
            # или 10 сс
            elif re.fullmatch(dec_number_pattern, term.word):
                arg = int(term.word)
                assert -2 ** 63 <= arg <= 2 ** 63 - 1, "Argument is not in range!"
                address -= 4
                code.append(
                    {
                        "address": address,
                        "opcode": self.word_to_opcode(terms[i - 1].word),
                        "arg": arg,
                        "term": term,
                    }

                )


            elif term.word == 'S"':
                i += 1
                string = ""
                while not terms[i].word.endswith('"'):
                    string += terms[i].word
                    string += " "
                    i += 1
                string += terms[i].word[:-1]

                code.append(
                    {
                        "address": address,
                        "opcode": Opcode.STORE,
                        "arg": chr(len(string)) + string,
                        "term": term,
                    }
                )


            # если встретили определение слова
            elif self.word_to_opcode(term.word) == Opcode.VARIABLE:
                # после обработки всех термов, мы добавим его в конец
                value = code[-1]["arg"]  # берем отсюда, так как тут число уже прошло конвертацию
                label = terms[i + 1].word
                self.variables_queue[label] = value
                i += 1  # перепрыгиваем через лейбл, тк мы его обработали
                code.pop()
                address -= 8

            # если встретили определение функции
            elif ":" in term.word:
                label = terms[i].word.split(":")[0]
                self.functions_map[label] = address
                # address -= 4
                i += 1
                continue

            # обработка if, чтобы вставить им потом в аругменты адреса переходов
            elif self.word_to_opcode(term.word) == Opcode.IF:
                brackets_stack.append({"address": address, "opcode": Opcode.IF})
                code.append({"address": address, "opcode": Opcode.IF, "arg": self.functions_map[terms[i + 1].word],
                             "term": term})
                i += 1

            # если встретили переменную или вызов функции
            elif term.word in self.second_type_instructions():
                # print("каким должно быть", term.word, address)
                arg = terms[i + 1].word
                if arg in self.variables_queue:
                    code.append(
                        {
                            "address": address,
                            "opcode": self.word_to_opcode(term.word),
                            "arg": arg,
                            "term": term,
                        }
                    )
                    i += 1
                elif arg in self.functions_map:
                    # print(arg)
                    code.append(
                        {
                            "address": address,
                            "opcode": self.word_to_opcode(term.word),
                            "arg": self.functions_map[arg],
                            "term": term,
                        }
                    )
                    i += 1
                elif arg in self.second_type_instructions():
                    # print("каким ", term.word, address)
                    code.append(
                        {
                            "address": address,
                            "opcode": self.word_to_opcode(term.word),
                            "arg": terms[i + 1].word,
                            "term": term,
                        }
                    )
                    i += 1
                # else:
                #    assert arg in self.variables_map or arg in self.functions_map, f"Label f'{arg}'is not defined!"
            else:
                # print(self.word_to_opcode(term.word), address)
                code.append({"address": address, "opcode": self.word_to_opcode(term.word), "term": term})
                address -= 3

            # if term.word in self.instr_without_arg():
            #    address -= 3

            i += 1
            address += 4
            # print(address)
        return code

    def translate_stage_2(self, code):

        """
        Вместо лейблов подставляются адреса,
        в if подставляются адреса переходов,
        переменные сохраняются после halt.
        """
        # сначала сохраним переменные в конце кода, чтобы потом подставлять их адреса
        curr_address = code[-1]["address"] + 1
        for label, value in self.variables_queue.items():
            self.variables_map[label] = curr_address
            code.append({"address": curr_address, "arg": value})
            if isinstance(value, int):
                if -2 ** 31 <= value <= 2 ** 31 - 1:
                    size = 4
                else:
                    size = 8
            elif isinstance(value, str):
                size = len(value) * 4
            curr_address += size

        for instruction in code:
            if "arg" in instruction:
                arg = instruction["arg"]
                if arg == -1:
                    instruction["arg"] = self.addresses_in_conditions[instruction["address"]]
                elif isinstance(arg, str) and "opcode" in instruction:

                    instruction["arg"] = self.variables_map[arg]
                    # если переменной с таким именем нет, транслятор выдаст ошибку еще на первом этапе

        return code

    def get_first_executable_instr(self):
        return self.functions_map["_start"]


def main(source, target):
    """Функция запуска транслятора. Параметры -- исходный и целевой файлы."""
    translator = Translator()
    with open(source, encoding="utf-8") as f:
        source = f.read()

    code = translator.translate_stage_1(source)

    code = translator.translate_stage_2(code)
    for instr in code:
        print(instr)
    first_ex_instr = translator.get_first_executable_instr()
    # print("first_ex_instr", first_ex_instr)
    binary_code = to_bytes(code, first_ex_instr)
    # print(binary_code)
    hex_code = to_hex(code, translator.variables_map)

    # Убедимся, что каталог назначения существует
    os.makedirs(os.path.dirname(os.path.abspath(target)) or ".", exist_ok=True)

    # Запишем выходные файлы
    with open(target, "wb") as f:
        f.write(binary_code)
    with open(target + ".hex", "w") as f:
        f.write(hex_code)
    with open(target + ".base64", "w") as f:
        f.write(base64.b64encode(binary_code).decode("utf-8"))

    print("source LoC:", len(source.split(" ")), "code instr:", len(code))


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)
