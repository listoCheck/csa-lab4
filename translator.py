import os
import sys
from isa import Opcode, Term, to_bytes, to_hex, write_json


def symbols():
    """Полное множество символов языка, включая слова."""
    return {
        "drop", "dup", "swap", "+", "-", "*", "/", "mod", "negate", "=", "<", ">", "and", "or", "xor", "invert",
        "if", "exit", "!", "@", "key"
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
        "exit": Opcode.EXIT,
        "!": Opcode.STORE,
        "@": Opcode.FETCH,
        "key": Opcode.KEY,
        "halt": Opcode.EXIT
    }.get(symbol)


def text2terms(text):
    """Трансляция текста в последовательность операторов языка (токенов), включая метки."""

    terms = []
    lines = text.splitlines()

    # 1-й проход: собираем все метки (без двоеточия)
    labels = set()
    for line_num, line in enumerate(lines, 1):
        for word in line.split():
            if word.endswith(":"):
                labels.add(word[:-1])

    # 2-й проход: сами термы
    for line_num, line in enumerate(lines, 1):
        for pos, word in enumerate(line.split(), 1):
            # если это определение метки или команда или ссылка на метку
            if word.endswith(":") or word in symbols() or word in labels:
                terms.append(Term(line_num, pos, word))

    # Для отладки можно раскомментировать:
    # print("TERMS:", terms)

    return terms




def translate(text):
    """Трансляция текста программы в машинный код с поддержкой меток."""
    terms = text2terms(text)

    # Собираем определения меток
    labels = {}
    pc_counter = 0
    for term in terms:
        if term.symbol.endswith(":"):
            label = term.symbol[:-1]
            assert label not in labels, f"Повторное определение метки: {label}"
            labels[label] = None  # адрес пока не известен
        else:
            pc_counter += 1
    # Теперь заполним реальные адреса (индексы)
    addr = 0
    for term in terms:
        if term.symbol.endswith(":"):
            labels[term.symbol[:-1]] = addr
        else:
            addr += 1

    # Отфильтруем только те термы, которые нам нужны
    filtered = [t for t in terms if not t.symbol.endswith(":")]

    # Генерим код инструкций
    code = []
    i = 0
    pc = 0
    while i < len(filtered):
        term = filtered[i]
        sym = term.symbol

        if sym == "if":
            # Обязательный следующий терм — метка
            assert i + 1 < len(filtered), f"После 'if' на строке {term.line} нет метки"
            label = filtered[i + 1].symbol
            assert label in labels, f"Метка не определена: {label}"
            code.append({
                "index": pc,
                "opcode": Opcode.IF,
                "arg": labels[label],
                "term": term
            })
            i += 2  # съели 'if' и метку
        else:
            # Пропускаем одиночные ссылки на метки, если вдруг остались
            if sym in labels:
                i += 1
                continue

            opcode = symbol2opcode(sym)
            assert opcode is not None, f"Неизвестная операция: {sym}"
            code.append({"index": pc, "opcode": opcode, "term": term})
            i += 1

        pc += 1

    # В конце — команда остановки
    code.append({"index": pc, "opcode": Opcode.HALT})
    print(code)
    return code



def main(source2, target2):
    """Функция запуска транслятора. Параметры -- исходный и целевой файлы."""
    with open(source2, encoding="utf-8") as f:
        source2 = f.read()

    code = translate(source2)
    binary_code = to_bytes(code)
    hex_code = to_hex(code)

    # Убедимся, что каталог назначения существует
    os.makedirs(os.path.dirname(os.path.abspath(target2)) or ".", exist_ok=True)

    # Запишем выходные файлы
    if target2.endswith(".bin"):
        with open(target2, "wb") as f:
            f.write(binary_code)
        with open(target2 + ".hex", "w") as f:
            f.write(hex_code)
    else:
        write_json(target2, code)

    print("source LoC:", len(source2.split("\n")), "code instr:", len(code))


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)
