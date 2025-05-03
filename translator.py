import os
import sys
from isa import Opcode, Term, to_bytes, to_hex, write_json


def symbols():
    """Полное множество символов языка, включая слова."""
    return {
        "drop", "dup", "swap", "+", "-", "*", "/", "mod", "negate", "=", "<", ">", "and", "or", "xor", "invert",
        "if", "else", "then", "begin", "until", "while", "repeat", "do", "loop", "leave", "exit", "!", "@",
        "allot", "emit", "key", ".", "cr", "halt"
    }

#asdasd
def symbol2opcode(symbol):
    """Отображение операторов исходного кода в коды операций."""
    return {
        "drop": Opcode.DROP,
        "dup": Opcode.DUP,
        "swap": Opcode.SWAP,
        "+": Opcode.ADD,
        "-": Opcode.SUB,
        "*": Opcode.MUL,
        "/": Opcode.DIV,
        "mod": Opcode.MOD,
        "negate": Opcode.NEGATE,
        "=": Opcode.EQUAL,
        "<": Opcode.LESS,
        ">": Opcode.GREATER,
        "and": Opcode.AND,
        "or": Opcode.OR,
        "xor": Opcode.XOR,
        "invert": Opcode.INVERT,
        "if": Opcode.IF,
        "else": Opcode.ELSE,
        "then": Opcode.THEN,
        "begin": Opcode.BEGIN,
        "until": Opcode.UNTIL,
        "while": Opcode.WHILE,
        "repeat": Opcode.REPEAT,
        "do": Opcode.DO,
        "loop": Opcode.LOOP,
        "leave": Opcode.EXIT,  # Здесь leave эквивалентен EXIT
        "exit": Opcode.EXIT,
        "!": Opcode.STORE,
        "@": Opcode.FETCH,
        "allot": Opcode.ALLOT,
        "emit": Opcode.EMIT,
        "key": Opcode.KEY,
        ".": Opcode.PRINT,
        "cr": Opcode.CR,
        "halt": Opcode.HALT,
    }.get(symbol)


def text2terms(text):
    """Трансляция текста в последовательность операторов языка (токенов).

    Включает в себя:

    - отсеивание всех незначимых символов (считаются комментариями);
    - проверка формальной корректности программы (парность оператора цикла).
    """
    terms = []
    lines = text.splitlines()

    for line_num, line in enumerate(lines, 1):
        words = line.split()
        for pos, word in enumerate(words, 1):
            if word in symbols():  # Проверяем наличие целого слова в наборе символов
                terms.append(Term(line_num, pos, word))

    return terms


def translate(text):
    """Трансляция текста программы в машинный код.

    Выполняется в два этапа:

    1. Трансляция текста в последовательность операторов языка (токенов).
    2. Генерация машинного кода.

        - Прямое отображение части операторов в машинный код.
    """
    terms = text2terms(text)

    # Транслируем термы в машинный код.
    code = []
    for pc, term in enumerate(terms):
        # Обработка тривиально отображаемых операций.
        code.append({"index": pc, "opcode": symbol2opcode(term.symbol), "term": term})

    # Добавляем инструкцию остановки процессора в конец программы.
    code.append({"index": len(code), "opcode": Opcode.HALT})
    print(code)
    return code


def main(source, target):
    """Функция запуска транслятора. Параметры -- исходный и целевой файлы."""
    with open(source, encoding="utf-8") as f:
        source = f.read()

    code = translate(source)
    binary_code = to_bytes(code)
    hex_code = to_hex(code)

    # Убедимся, что каталог назначения существует
    os.makedirs(os.path.dirname(os.path.abspath(target)) or ".", exist_ok=True)

    # Запишим выходные файлы
    if target.endswith(".bin"):
        with open(target, "wb") as f:
            f.write(binary_code)
        with open(target + ".hex", "w") as f:
            f.write(hex_code)
    else:
        write_json(target, code)

    print("source LoC:", len(source.split("\n")), "code instr:", len(code))


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)
