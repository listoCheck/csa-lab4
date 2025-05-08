import os
import sys
from isa import Opcode, Term, to_bytes, to_hex, write_json


def symbols():
    return {
        "drop", "dup", "swap", "+", "-", "*", "/", "mod", "negate", "=", "<", ">", "and", "or", "xor", "invert",
        "if", "exit", "!", "@", "key", "halt", "lit", "emit", "jump"
    }


def symbol2opcode(symbol):
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
        "halt": Opcode.HALT,
        "lit": Opcode.LIT,
        "emit": Opcode.EMIT,
        "JUMP": Opcode.JUMP,
    }.get(symbol)


def text2terms(text):
    terms = []
    lines = text.splitlines()
    print("\nПолученный код:")
    print("\n".join(str(i) for i in lines))
    # Сначала найдём все метки
    labels = set()
    for line_num, line in enumerate(lines, 1):
        for word in line.split():
            if word.endswith(":"):
                labels.add(word[:-1])

    # Парсим термы
    ic = 0
    for line_num, line in enumerate(lines, 1):
        words = line.split()
        for pos, word in enumerate(words, 1):
            if word in symbols():
                ic += 1
            if word.endswith(":") or word in symbols() or word in labels:
                terms.append(Term(line_num, pos, word))
                print(Term(line_num, pos, word))
            else:
                try:
                    int(word)  # если это число
                    terms.append(Term(line_num, pos, word))
                except ValueError:
                    pass  # не команда, не метка, не число — пропускаем
    return terms, ic


def translate(text):
    terms, normal_numeration = text2terms(text)

    labels = {}
    pc_counter = 0
    for term in terms:
        if term.symbol.endswith(":"):
            label = term.symbol[:-1]
            assert label not in labels, f"Повторное определение метки: {label}"
            labels[label] = None
        else:
            pc_counter += 1

    # Присваиваем меткам правильные адреса
    addr = 0
    for term in terms:
        if term.symbol.endswith(":"):
            labels[term.symbol[:-1]] = addr
        else:
            addr += 1

    new_labels = {}
    for i in range(len(terms)):
        counter = 0
        if terms[i].symbol.endswith(":"):
            for j in range(i):
                if terms[j].symbol in ("if", "lit", "jump"):
                    counter += 1
            new_labels[terms[i].symbol[:-1]] = labels[terms[i].symbol[:-1]] - counter

    filtered = [t for t in terms if not t.symbol.endswith(":")]

    code = []
    i = 0
    pc = 0
    ic = 0

    while i < len(filtered):

        term = filtered[i]
        sym = term.symbol

        if sym == "if":
            assert i + 1 < len(filtered), f"После 'if' на строке {term.line} нет метки"
            label = filtered[i + 1].symbol
            assert label in labels, f"Метка не определена: {label}"
            print("asdasd", labels[label], normal_numeration)
            code.append({
                "index": pc,
                "opcode": Opcode.IF,
                "arg": new_labels[label],
                "term": term
            })
            i += 2
            ic += 1
        elif sym == "lit":
            assert i + 1 < len(filtered), f"После 'lit' на строке {term.line} нет значения"
            value_term = filtered[i + 1]
            try:
                value = int(value_term.symbol)
            except ValueError:
                raise AssertionError(f"Некорректное значение после 'lit': {value_term.symbol} на строке {value_term.line}")
            code.append({
                "index": pc,
                "opcode": Opcode.LIT,
                "arg": value,
                "term": term
            })
            i += 2
        elif sym == "jump":
            assert i + 1 < len(filtered), f"После 'if' на строке {term.line} нет метки"
            label = filtered[i + 1].symbol
            assert label in labels, f"Метка не определена: {label}"
            code.append({
                "index": pc,
                "opcode": Opcode.JUMP,
                "arg": new_labels[label],
                "term": term
            })
            i += 2
        else:
            if sym in labels:
                i += 1
                continue
            opcode = symbol2opcode(sym)
            assert opcode is not None, f"Неизвестная операция: {sym}"
            code.append({"index": pc, "opcode": opcode, "term": term})
            i += 1

        pc += 1

    if not code or code[-1]["opcode"] != Opcode.HALT:
        code.append({"index": pc, "opcode": Opcode.HALT})

    print("\nМетки:")
    print(labels, '\n')
    print("\nКод")
    print("\n".join(str(i) for i in code))
    return code



def main(source2, target2):
    with open(source2, encoding="utf-8") as f:
        source2 = f.read()

    code = translate(source2)
    binary_code = to_bytes(code)
    hex_code = to_hex(code)

    print("\nБайткод")
    print(hex_code)
    os.makedirs(os.path.dirname(os.path.abspath(target2)) or ".", exist_ok=True)

    if target2.endswith(".bin"):
        with open(target2, "wb") as f:
            f.write(binary_code)
        with open(target2 + ".hex", "w") as f:
            f.write(hex_code)
    else:
        write_json(target2, code)

    print("\nsource LoC:", len(source2.split("\n")), "code instr:", len(code))


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)
