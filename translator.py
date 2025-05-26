import os
import sys
from isa import Opcode, Term, to_bytes, to_hex, write_json


def symbols():
    return {
        "drop", "dup", "swap", "+", "-", "*", "/", "mod", "negate", "=", "<", ">", "and", "or", "xor", "invert",
        "if", "!", "@", "key", "halt", "lit", "emit", "jump", "call", "ret", "c"
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
        "!": Opcode.STORE,
        "@": Opcode.FETCH,
        "key": Opcode.KEY,
        "halt": Opcode.HALT,
        "lit": Opcode.LIT,
        "emit": Opcode.EMIT,
        "jump": Opcode.JUMP,
        "call": Opcode.CALL,
        "ret": Opcode.RET,
        "c": Opcode.CARRY,
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
    for line_num, line in enumerate(lines, 1):
        words = line.split()
        for pos, word in enumerate(words, 1):
            if ";" in word:
                word = word.split(";")[0]
            if word.endswith(":") or word in symbols() or word in labels:
                terms.append(Term(line_num, pos, word))
            else:
                try:
                    if "0x" in word:
                        int(word, 16)
                    else:
                        int(word)
                    terms.append(Term(line_num, pos, word))
                except ValueError:
                    pass
    return terms


def translate(text):
    terms = text2terms(text)

    labels = {}
    pc_counter = 0
    print(terms)
    for term in terms:
        if term.symbol.endswith(":"):
            label = term.symbol[:-1]
            assert label not in labels, f"Повторное определение метки: {label}"
            labels[label] = None
        else:
            pc_counter += 1

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
                if terms[j].symbol in ("if", "lit", "jump", "call", "key", "emit"):
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

        def expect_next_token():
            assert i + 1 < len(filtered), f"После '{sym}' на строке {term.line} нет аргумента"
            return filtered[i + 1]

        def resolve_label(label_term):
            label = label_term.symbol
            assert label in labels, f"Метка не определена: {label}"
            return new_labels[label]

        if sym in {"if", "jump", "call"}:
            arg_term = expect_next_token()
            target = resolve_label(arg_term)
            opcode = Opcode[sym.upper()]
            code.append({
                "index": pc,
                "opcode": opcode,
                "arg": target,
                "term": term
            })
            i += 2
            ic += 1 if sym == "if" else ic

        elif sym == "lit":
            value_term = expect_next_token()
            try:
                value = int(value_term.symbol, 16) if "0x" in value_term.symbol else int(value_term.symbol)
            except ValueError:
                raise AssertionError(
                    f"Некорректное значение после 'lit': {value_term.symbol} на строке {value_term.line}")
            code.append({
                "index": pc,
                "opcode": Opcode.LIT,
                "arg": value,
                "term": term
            })
            i += 2

        elif sym in {"key", "emit"}:
            port_term = expect_next_token()
            try:
                port = int(port_term.symbol)
            except ValueError:
                raise AssertionError(
                    f"Некорректный номер порта после '{sym}': {port_term.symbol} на строке {port_term.line}")
            opcode = Opcode[sym.upper()]
            code.append({
                "index": pc,
                "opcode": opcode,
                "arg": port,
                "term": term
            })
            i += 2

        else:
            if sym in labels:
                i += 1
                continue
            opcode = symbol2opcode(sym)
            assert opcode is not None, f"Неизвестная операция: {sym}"
            code.append({
                "index": pc,
                "opcode": opcode,
                "term": term
            })
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

