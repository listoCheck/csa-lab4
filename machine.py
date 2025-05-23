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
    b = None

    def __init__(self, data_memory_size, input_buffer, program):
        self.program = program
        self.program_counter = 0
        assert data_memory_size > 0, "Data_memory size should be non-zero"
        self.program_memory_size = len(program)
        self.data_memory_size = data_memory_size
        self.data_memory = program + [0] * data_memory_size
        self.stack = [0, 0]
        self.stack_first = 0
        self.stack_second = 0
        self.input_buffer = input_buffer
        self.output_buffer = []
        self.a = 0
        self.tos = 0
        self.b = []

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
        self.stack = self.stack[:-2]

    def read_from_memory(self):
        addr = self.stack[-1] + self.program_memory_size
        self.stack = self.stack[:-1]
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

    def push_b(self):
        self.b.append(self.program_counter)

    def pop_b(self):
        self.tos = self.b[-1]
        self.b = self.b[:-1]

    def tos_to_pc(self):
        self.program_counter = self.tos


# надо сделать схему с вентилями и дальше в логгинге выполнения каждый команды написать какие вентили под нее я открываю
class ControlUnit:
    program = None  # Память команд.
    data_path = None  # Блок обработки данных.
    _tick = None  # Текущее модельное время процессора (в тактах). Инициализируется нулём.
    input_index = None
    mpc = None

    def __init__(self, data_path):
        self.mpc = 0
        self.data_path = data_path
        self._tick = 0
        self.step = 0
        self.input_index = 0
        self.halted = False
        self.rep_swap_dup = False

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
        print(opcode)
        self.mpc = mapping.get(opcode, [])
        print(self.mpc)
        prev_mpc = self.mpc
        mc = mp[prev_mpc]
        mc(self, instr)
        while prev_mpc != self.mpc:
            prev_mpc = self.mpc
            mc = mp[self.mpc]
            mc(self, instr)
            self.tick()

        if not self.halted and opcode not in (Opcode.JUMP, Opcode.EXIT, Opcode.HALT, Opcode.CALL):
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
        self.data_path.tos = self.data_path.stack[-1]
        self.data_path.a = self.data_path.stack[-1]
        self.data_path.stack = self.data_path.stack[:-1]
        self.mpc -=  26
        self.rep_swap_dup = True

    # SWAP: меняет местами верхние два элемента стека
    def micro_swap(self, instr):
        print(f"[tick {self._tick}] SWAP")
        self.micro_tos(instr)
        self.mpc += 1
        self.rep_swap_dup = True

    # ADD
    def micro_add_1(self, instr):
        print(f"[tick {self._tick}] ADD")
        self.micro_tos(instr)
        self.data_path.alu("+")
        self.mpc -= 2

    # SUB
    def micro_sub_1(self, instr):
        print(f"[tick {self._tick}] SUB")
        self.micro_tos(instr)
        self.data_path.alu("-")
        self.mpc -= 3

    # MUL
    def micro_mul_1(self, instr):
        print(f"[tick {self._tick}] MUL")
        self.micro_tos(instr)
        self.data_path.alu("*")
        self.mpc -= 4

    # DIV
    def micro_div_1(self, instr):
        print(f"[tick {self._tick}] DIV")
        self.micro_tos(instr)
        self.data_path.alu("/")
        self.mpc -= 5

    # MOD
    def micro_mod_1(self, instr):
        print(f"[tick {self._tick}] MOD")
        self.micro_tos(instr)
        self.data_path.alu("%")
        self.mpc -= 6

    # NEGATE
    def micro_negate(self, instr):
        print(f"[tick {self._tick}] NEGATE")
        self.micro_tos(instr)
        self.data_path.alu("--")
        self.mpc -= 7

    # EQUAL (=)
    def micro_equal(self, instr):
        print(f"[tick {self._tick}] EQUAL")
        self.micro_tos(instr)
        self.data_path.alu("==")
        self.mpc -= 8

    # LESS (<)
    def micro_less(self, instr):
        print(f"[tick {self._tick}] LESS")
        self.micro_tos(instr)
        self.data_path.alu(">")
        self.mpc -= 9

    # GREATER (>)
    def micro_greater(self, instr):
        print(f"[tick {self._tick}] GREATER")
        self.micro_tos(instr)
        self.data_path.alu("<")
        self.mpc -= 10

    # AND
    def micro_and(self, instr):
        print(f"[tick {self._tick}] AND")
        self.micro_tos(instr)
        self.data_path.alu("&")
        self.mpc -= 11

    # OR
    def micro_or(self, instr):
        print(f"[tick {self._tick}] OR")
        self.micro_tos(instr)
        self.data_path.alu("|")
        self.mpc -= 12

    # XOR
    def micro_xor(self, instr):
        print(f"[tick {self._tick}] XOR")
        self.micro_tos(instr)
        self.data_path.alu("^")
        self.mpc -= 13

    # INVERT
    def micro_invert(self, instr):
        print(f"[tick {self._tick}] INVERT")
        self.data_path.alu("~")
        self.mpc -= 14

    # IF (условный переход, реализуем как простой переход, если acc != 0)
    def micro_if_1(self, instr):
        print(f"[tick {self._tick}] IF - проверка условия")
        self.micro_tos(instr)
        self.mpc += 1
        print("tos:", self.data_path.tos)

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
        self.mpc -= 17

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
        self.mpc -= 18

    # HALT
    def micro_halt(self, instr):
        print(f"[tick {self._tick}] HALT")
        self.halted = True

    # LIT - загрузить литерал из инструкции
    def micro_lit_1(self, instr):
        print(f"[tick {self._tick}] LIT - подготовка")
        print(f"[tick {self._tick}] IR[arg] -> BUS")
        self.mpc += 1

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

    def save_comeback_adr(self, instr):
        print(f"[tick {self._tick}] COMEBACK ADR")
        self.data_path.push_b()
        self.mpc += 1

    # JUMP - перейти на адрес, заданный в аргументе инструкции
    def micro_jump_1(self, instr):
        print(f"[tick {self._tick}] JUMP")
        target = instr.get("arg", 0)
        print(f"Jump to {target}")
        self.data_path.program_counter = target

    def micro_tos(self, instr):
        print(f"[tick {self._tick}] FIRST_STACK -> TOS")
        self.data_path.write_tos()
        return

    def micro_stack_to_a(self, instr):
        print(f"[tick {self._tick}] FIRST_STACK -> A")
        self.data_path.stack_to_a()
        self.mpc += 1

    def micro_a_to_tos(self, instr):
        print(f"[tick {self._tick}] A -> TOS")
        self.data_path.a_to_tos()
        self.mpc -= 1

    def micro_tos_to_stack(self, instr):
        print(f"[tick {self._tick}] TOS -> FIRST_STACK")
        self.data_path.save_tos()
        if self.rep_swap_dup:
            self.mpc += 1
            self.rep_swap_dup = False


    def micro_ret(self, insr):
        print(f"[tick {self._tick}] RET")
        self.data_path.pop_b()
        self.data_path.tos_to_pc()

    def __str__(self):
        return (f"Tick: {self._tick}, "
                f"PC: {self.data_path.program_counter}, "
                f"Stack: [{self.data_path.stack[-1]}, {self.data_path.stack[-2]}], "
                f"Input: {self.data_path.input_buffer}, "
                f"Output: {self.data_path.output_buffer}, "
                f"tos: {self.data_path.tos}, "
                f"a: {self.data_path.a}, "
                f"b: {self.data_path.b}")

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
        # print(self.data_path.program_counter, len(self.data_path.program) - 1)
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


# Программа микрокода - список списков сигналов
mp = [
    ControlUnit.micro_swap,
    ControlUnit.micro_stack_to_a,
    ControlUnit.micro_tos_to_stack,
    ControlUnit.micro_a_to_tos,
    ControlUnit.micro_add_1,
    ControlUnit.micro_sub_1,
    ControlUnit.micro_mul_1,
    ControlUnit.micro_div_1,
    ControlUnit.micro_mod_1,
    ControlUnit.micro_negate,
    ControlUnit.micro_equal,
    ControlUnit.micro_less,
    ControlUnit.micro_greater,
    ControlUnit.micro_and,
    ControlUnit.micro_or,
    ControlUnit.micro_xor,
    ControlUnit.micro_invert,
    ControlUnit.micro_if_1,
    ControlUnit.micro_if_2,
    ControlUnit.micro_fetch_1,
    ControlUnit.micro_key_1,
    ControlUnit.micro_store_1,
    ControlUnit.micro_lit_1,
    ControlUnit.micro_lit_2,
    ControlUnit.save_comeback_adr,
    ControlUnit.micro_jump_1,
    ControlUnit.micro_ret,
    ControlUnit.micro_drop,
    ControlUnit.micro_dup,
    ControlUnit.micro_emit_1,
    ControlUnit.micro_halt
]

mapping = {
    Opcode.SWAP: 0,
    Opcode.ADD: 4,
    Opcode.SUB: 5,
    Opcode.MUL: 6,
    Opcode.DIV: 7,
    Opcode.MOD: 8,
    Opcode.NEGATE: 9,
    Opcode.EQUAL: 10,
    Opcode.LESS: 11,
    Opcode.GREATER: 12,
    Opcode.AND: 13,
    Opcode.OR: 14,
    Opcode.XOR: 15,
    Opcode.INVERT: 16,
    Opcode.IF: 17,
    Opcode.FETCH: 19,
    Opcode.KEY: 20,
    Opcode.STORE: 21,
    Opcode.LIT: 22,
    Opcode.CALL: 24,
    Opcode.JUMP: 25,
    Opcode.RET: 26,
    Opcode.DROP: 27,
    Opcode.DUP: 28,
    Opcode.EMIT: 29,
    Opcode.HALT: 30
}


def main(code_file, input_file):
    with open(code_file, "r", encoding="utf-8") as file:
        text_code = file.read()
    code = from_bytes(text_code)
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
