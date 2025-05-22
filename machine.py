import logging
import sys

from isa import Opcode, from_bytes, opcode_to_binary


class Datapath:
    stack_first = None  # Верхняя ячейка стека
    stack_second = None  # Нижняя ячейка стека
    input_buffer = None  # Буфер входных данных. Инициализируется входными данными конструктора.
    output_buffer = None  # Буфер выходных данных.
    data_memory_size = None  # Размер памяти данных.
    data_memory = None  # Память данных. Инициализируется нулевыми значениями.
    a = None
    tos = None
    program_memory_size = None

    def __init__(self, data_memory_size, input_buffer, program):
        self.program = program
        self.program_counter = 0
        assert data_memory_size > 0, "Data_memory size should be non-zero"
        self.program_memory_size = len(program)
        self.data_memory_size = data_memory_size
        self.data_memory = program + [0] * data_memory_size
        self.stack = [0, 0]
        # self.stack_first = self.stack[-1]
        # self.stack_second = self.stack[-2]
        self.stack_first = 0
        self.stack_second = 0
        self.input_buffer = input_buffer
        self.output_buffer = []
        self.a = 0
        self.tos = 0

    def put_in_output_buffer(self, char):
        self.output_buffer.append(char)

    def write_in_memory(self):
        addr = self.stack[-2] + self.program_memory_size
        val = self.stack[-1]
        if 0 <= addr < self.data_memory_size:
            self.data_memory[addr] = val
            print(f"Store {val} to address {addr}")
        else:
            raise Exception("Store address out of range")

    def read_from_memory(self):
        addr = self.stack[-1] + self.program_memory_size
        if 0 <= addr < self.data_memory_size:
            val = self.data_memory[addr]
            print(f"Fetched {val} from address {addr}")
        else:
            raise Exception("Fetch address out of range")
        return val

    def flag_zero(self):
        if self.tos == 0:
            return True
        else:
            return False

    def write_tos(self):
        self.tos = self.stack[-1]
        print(self.tos)
        self.stack = self.stack[:-1]

    def stack_to_a(self):
        self.a = self.stack[-1]
        self.stack = self.stack[:-1]

    def a_to_tos(self):
        self.tos = self.a

    def save_tos(self):
        self.stack.append(self.tos)

    def alu(self, operand):
        value = 0
        self.stack_first = self.stack[-1]
        if operand == "+":
            value = self.stack_first + self.tos
            self.stack = self.stack[:-1]
        if operand == "-":
            value = self.tos - self.stack_first
            self.stack = self.stack[:-1]
        if operand == "*":
            value = self.tos * self.stack_first
            self.stack = self.stack[:-1]
        if operand == "/":
            if self.tos == 0:
                raise Exception("Division by zero")
            value = self.tos / self.stack_first
            self.stack = self.stack[:-1]
        if operand == "~":
            value = ~self.tos
        if operand == "%":
            value = self.tos % self.stack_first
            self.stack = self.stack[:-1]
        if operand == "&":
            value = self.tos & self.stack_first
            self.stack = self.stack[:-1]
        if operand == "|":
            value = self.tos | self.stack_first
            self.stack = self.stack[:-1]
        if operand == "^":
            value = self.tos ^ self.stack_first
            self.stack = self.stack[:-1]
        if operand == "--":
            value = -self.tos
        if operand == "==":
            value = int(self.tos == self.stack_first)
            self.stack = self.stack[:-1]
        if operand == ">":
            value = int(self.tos > self.stack_first)
            self.stack = self.stack[:-1]
        if operand == "<":
            value = int(self.tos < self.stack_first)
            self.stack = self.stack[:-1]
        self.tos = value

    def stack_push(self, value):
        self.stack.append(value)

    def stack_pop(self):
        self.stack_first = 0

    def save_to_reg_a(self):
        self.a = self.stack_first

    def move(self):
        self.stack_first = self.stack_second
        self.stack_second = 0


# надо сделать схему с вентилями и дальше в логгинге выполнения каждый команды написать какие вентили под нее я открываю
class ControlUnit:
    program = None  # Память команд.
    data_path = None  # Блок обработки данных.
    _tick = None  # Текущее модельное время процессора (в тактах). Инициализируется нулём.
    input_index = None

    def __init__(self, data_path):
        self.mpc = 0
        self.data_path = data_path
        self._tick = 0
        self.step = 0
        self.input_index = 0
        self.halted = False

    def tick(self):
        """Продвинуть модельное время процессора вперёд на один такт."""
        self._tick += 1

    def get_tick(self):
        return self._tick

    def new_input_index(self):
        self.input_index += 1

    def process_next_tick(self):
        if self.halted:
            raise StopIteration()

        if self.data_path.program_counter >= self.data_path.program_memory_size:
            raise StopIteration()

        instr = self.data_path.data_memory[self.data_path.program_counter]
        opcode = instr["opcode"]
        microcmds = microprogram.get(opcode, [])
        for microcmd in microcmds:
            microcmd(self, instr)
            self.tick()
        if not self.halted and opcode not in (Opcode.JUMP, Opcode.EXIT, Opcode.HALT):
            self.data_path.program_counter += 1

    def micro_push(self, instr):
        print(f"[tick {self._tick}] PUSH")
        self.data_path.stack_push()

    # --- Микрокоманды для каждой инструкции ---
    # DROP: удаляет верхний элемент стека (stack_first)
    def micro_drop(self, instr):
        print(f"[tick {self._tick}] DROP")
        self.data_path.stack_pop()

    # DUP: дублирует верхний элемент стека
    def micro_dup(self, instr):
        print(f"[tick {self._tick}] DUP")
        self.data_path.stack_push(self.data_path.stack_first)

    # SWAP: меняет местами верхние два элемента стека
    def micro_swap(self, instr):
        print(f"[tick {self._tick}] SWAP")
        self.data_path.alu("o")

    # ADD
    def micro_add_1(self, instr):
        print(f"[tick {self._tick}] ADD")
        self.data_path.alu("+")

    # SUB
    def micro_sub_1(self, instr):
        print(f"[tick {self._tick}] SUB")
        self.data_path.alu("-")

    # MUL
    def micro_mul_1(self, instr):
        print(f"[tick {self._tick}] MUL")
        self.data_path.alu("*")

    # DIV
    def micro_div_1(self, instr):
        print(f"[tick {self._tick}] DIV")
        self.data_path.alu("/")

    # MOD
    def micro_mod_1(self, instr):
        print(f"[tick {self._tick}] MOD")
        self.data_path.alu("%")

    # NEGATE
    def micro_negate(self, instr):
        print(f"[tick {self._tick}] NEGATE")
        self.data_path.alu("--")

    # EQUAL (=)
    def micro_equal(self, instr):
        print(f"[tick {self._tick}] EQUAL")
        self.data_path.alu("==")

    # LESS (<)
    def micro_less(self, instr):
        print(f"[tick {self._tick}] LESS")
        self.data_path.alu(">")

    # GREATER (>)
    def micro_greater(self, instr):
        print(f"[tick {self._tick}] GREATER")
        self.data_path.alu("<")

    # AND
    def micro_and(self, instr):
        print(f"[tick {self._tick}] AND")
        self.data_path.alu("&")

    # OR
    def micro_or(self, instr):
        print(f"[tick {self._tick}] OR")
        self.data_path.alu("|")

    # XOR
    def micro_xor(self, instr):
        print(f"[tick {self._tick}] XOR")
        self.data_path.alu("^")

    # INVERT
    def micro_invert(self, instr):
        print(f"[tick {self._tick}] INVERT")
        self.data_path.alu("~")

    # IF (условный переход, реализуем как простой переход, если acc != 0)
    def micro_if_1(self, instr):
        print(f"[tick {self._tick}] IF - проверка условия")
        self.data_path.tos = self.data_path.stack[-1]

    def micro_if_2(self, instr):
        addr = instr['arg']
        if self.data_path.flag_zero():
            self.data_path.program_counter = addr
            print(f"[tick {self._tick}] IF - переход на {addr}")
        else:
            print(f"[tick {self._tick}] IF - переход не требуется (не ноль)")

    # STORE - записать в память по адресу в stack_second значение из stack_first
    def micro_store_1(self, instr):
        print(f"[tick {self._tick}] STORE")
        self.data_path.write_in_memory()

    # FETCH - загрузить в стек значение из памяти по адресу stack_first
    def micro_fetch_1(self, instr):
        print(f"[tick {self._tick}] FETCH")
        self.data_path.tos = self.data_path.read_from_memory()

    # KEY - получить символ из входного буфера
    def micro_key_1(self, instr):
        print(f"[tick {self._tick}] KEY")
        if self.data_path.input_buffer:
            ch = self.data_path.input_buffer.pop(0)
            self.data_path.tos = ord(ch)
            print(f"Read char '{ch}' (code {ord(ch)})")
        else:
            self.data_path.tos = 0
            print("Input buffer empty")

    # HALT
    def micro_halt(self, instr):
        print(f"[tick {self._tick}] HALT")
        self.halted = True

    # LIT - загрузить литерал из инструкции
    def micro_lit_1(self, instr):
        print(f"[tick {self._tick}] LIT - подготовка")
        print(f"[tick {self._tick}] IR[arg] -> BUS")

    def micro_lit_2(self, instr):
        print(f"[tick {self._tick}] LIT - загрузка значения {instr['arg']}")
        print(f"[tick {self._tick}] BUS -> TOS")
        print(f"[tick {self._tick}] TOS -> STACK")
        self.data_path.stack_push(instr['arg'])

    # EMIT - выводить символ из stack_first
    def micro_emit_1(self, instr):
        print(f"[tick {self._tick}] EMIT")
        value = chr(self.data_path.stack[-1])
        self.data_path.put_in_output_buffer(value)
        print(f"Output char '{value}'")
        self.data_path.stack = self.data_path.stack[:-1]

    # JUMP - перейти на адрес, заданный в аргументе инструкции
    def micro_jump_1(self, instr):
        print(f"[tick {self._tick}] JUMP")
        target = instr.get("arg", 0)
        print(f"Jump to {target}")
        self.data_path.program_counter = target

    def micro_jump_2(self, instr):
        self.mpc = -1

    def micro_tos(self, instr):
        print(f"[tick {self._tick}] FIRST_STACK -> TOS")
        self.data_path.write_tos()

    def micro_stack_to_a(self, instr):
        print(f"[tick {self._tick}] FIRST_STACK -> A")
        self.data_path.stack_to_a()

    def micro_a_to_tos(self, instr):
        print(f"[tick {self._tick}] A -> TOS")
        self.data_path.a_to_tos()

    def micro_tos_to_stack(self, instr):
        print(f"[tick {self._tick}] TOS -> FIRST_STACK")
        self.data_path.save_tos()

    def __str__(self):
        return (f"Tick: {self._tick}, "
                f"PC: {self.data_path.program_counter}, "
                f"Stack: [{self.data_path.stack[-1]}, {self.data_path.stack[-2]}], "
                f"Input: {self.data_path.input_buffer}, "
                f"Output: {self.data_path.output_buffer}, "
                f"tos: {self.data_path.tos}, "
                f"a: {self.data_path.a}")

    def __repr__(self):
        state_repr = "TICK: {:3} PC: {:3} ADDR: {:3} MEM[ADDR]: {:3} STACK: [{}, {}] A: {}".format(
            self._tick,
            self.data_path.program_counter,
            self.data_path.data_address,
            self.data_path.data_memory[self.data_path.data_address],
            self.data_path.stack_first,
            self.data_path.stack_second,
            self.data_path.a,
        )
        #print(self.data_path.program_counter, len(self.data_path.program) - 1)
        if self.data_path.program_counter < len(self.data_path.program) - 1:
            instr = self.data_path.program[self.data_path.program_counter]
            opcode = instr["opcode"]
            instr_repr = str(opcode)
            if "arg" in instr:
                instr_repr += " {}".format(instr["arg"])

            instr_hex = f"{opcode_to_binary[opcode] << 24 | (instr.get('arg', 0) & 0x00FFFFFF):08X}"

            return "{} \t{} [{}]".format(state_repr, instr_repr, instr_hex)


def simulation(code, input_tokens, data_memory_size, limit):
    data_path = Datapath(data_memory_size, input_tokens, code)
    control_unit = ControlUnit(data_path)

    logging.debug("%s", control_unit)
    try:
        while control_unit.get_tick() < limit:
            control_unit.process_next_tick()
            logging.debug("%s", control_unit)
    except EOFError:
        logging.warning("Input buffer is empty!")
    except StopIteration:
        pass

    if control_unit.get_tick() >= limit:
        logging.warning("Tick limit exceeded!")

    return "".join(data_path.output_buffer), control_unit.get_tick()


def mpc_of_opcode(opcode: int) -> int:
    mapping = {
        Opcode.DROP: 0,
        Opcode.DUP: 1,
        Opcode.SWAP: 2,
        Opcode.ADD: 3,
        Opcode.SUB: 4,
        Opcode.MUL: 5,
        Opcode.DIV: 6,
        Opcode.MOD: 7,
        Opcode.NEGATE: 8,
        Opcode.EQUAL: 9,
        Opcode.LESS: 10,
        Opcode.GREATER: 11,
        Opcode.AND: 12,
        Opcode.OR: 13,
        Opcode.XOR: 14,
        Opcode.INVERT: 15,
        Opcode.IF: 16,
        Opcode.EXIT: 17,
        Opcode.STORE: 18,
        Opcode.FETCH: 19,
        Opcode.KEY: 20,
        Opcode.HALT: 21,
        Opcode.LIT: 22,
        Opcode.EMIT: 23,
        Opcode.JUMP: 24,
    }
    return mapping.get(opcode, 0)


# Программа микрокода - список списков сигналов
microprogram = {
    Opcode.DROP: [ControlUnit.micro_drop],
    Opcode.DUP: [ControlUnit.micro_dup],
    Opcode.SWAP: [ControlUnit.micro_tos, ControlUnit.micro_stack_to_a, ControlUnit.micro_tos_to_stack,
                  ControlUnit.micro_a_to_tos, ControlUnit.micro_tos_to_stack],
    Opcode.ADD: [ControlUnit.micro_tos, ControlUnit.micro_add_1, ControlUnit.micro_tos_to_stack],
    Opcode.SUB: [ControlUnit.micro_tos, ControlUnit.micro_sub_1, ControlUnit.micro_tos_to_stack],
    Opcode.MUL: [ControlUnit.micro_tos, ControlUnit.micro_mul_1, ControlUnit.micro_tos_to_stack],
    Opcode.DIV: [ControlUnit.micro_tos, ControlUnit.micro_div_1, ControlUnit.micro_tos_to_stack],
    Opcode.MOD: [ControlUnit.micro_tos, ControlUnit.micro_mod_1, ControlUnit.micro_tos_to_stack],
    Opcode.NEGATE: [ControlUnit.micro_tos, ControlUnit.micro_negate, ControlUnit.micro_tos_to_stack],
    Opcode.EQUAL: [ControlUnit.micro_tos, ControlUnit.micro_equal, ControlUnit.micro_tos_to_stack],
    Opcode.LESS: [ControlUnit.micro_tos, ControlUnit.micro_less, ControlUnit.micro_tos_to_stack],
    Opcode.GREATER: [ControlUnit.micro_tos, ControlUnit.micro_greater, ControlUnit.micro_tos_to_stack],
    Opcode.AND: [ControlUnit.micro_tos, ControlUnit.micro_and, ControlUnit.micro_tos_to_stack],
    Opcode.OR: [ControlUnit.micro_tos, ControlUnit.micro_or, ControlUnit.micro_tos_to_stack],
    Opcode.XOR: [ControlUnit.micro_tos, ControlUnit.micro_xor, ControlUnit.micro_tos_to_stack],
    Opcode.INVERT: [ControlUnit.micro_tos, ControlUnit.micro_invert, ControlUnit.micro_tos_to_stack],
    Opcode.IF: [ControlUnit.micro_tos, ControlUnit.micro_if_2, ControlUnit.micro_tos_to_stack],
    Opcode.STORE: [ControlUnit.micro_store_1],
    Opcode.FETCH: [ControlUnit.micro_fetch_1, ControlUnit.micro_tos_to_stack],
    Opcode.KEY: [ControlUnit.micro_key_1, ControlUnit.micro_tos_to_stack],
    Opcode.HALT: [ControlUnit.micro_halt],
    Opcode.LIT: [ControlUnit.micro_lit_1, ControlUnit.micro_lit_2],
    Opcode.EMIT: [ControlUnit.micro_emit_1],
    Opcode.JUMP: [ControlUnit.micro_jump_1, ControlUnit.micro_jump_2],
}


def main(code_file, input_file):
    with open(code_file, "r", encoding="utf-8") as file:
        text_code = file.read()
    code = from_bytes(text_code)
    print(code)
    with open(input_file, encoding="utf-8") as file:
        input_text = file.read()
        input_tokens = list(input_text)

    output, ticks = simulation(code, input_tokens, data_memory_size=100, limit=2000)
    print(output)
    print("ticks:", ticks)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    assert len(sys.argv) == 3, "Usage: machine.py <code_file> <input_file>"
    _, code_file, input_file = sys.argv
    main(code_file, input_file)
