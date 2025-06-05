import logging
import os
import sys

from isa import Opcode, bin_to_opcode


class Datapath:
    stack_first = None  # Верхняя ячейка стека
    stack_second = None  # Нижняя ячейка стека
    input_buffer0 = None  # Буфер входных данных. Инициализируется входными данными конструктора.
    output_buffer0 = None  # Буфер выходных данных.
    data_memory_size = None  # Размер памяти данных.
    data_memory = None  # Память данных. Инициализируется нулевыми значениями.
    a = None
    program_memory_size = None
    return_stack = None

    def __init__(self, data_memory_size, input_buffer0, program, code_len):
        self.code_len = code_len
        self.program = program
        self.program_counter = 0
        assert data_memory_size > 0, "Data_memory size should be non-zero"
        self.program_memory_size = 0
        self.data_memory_size = data_memory_size
        self.input_buffer0 = input_buffer0
        self.input_buffer1 = []
        self.output_buffer0 = []
        self.output_buffer1 = []
        self.data_memory = program + [0 for i in range(data_memory_size)]
        self.stack = [0, 0]
        self.stack_first = 0
        self.stack_second = 0
        self.a = 0
        self.carry = 0
        self.return_stack = []
        self.INT32_MIN = -2 ** 31
        self.INT32_MAX = 2 ** 31 - 1
        self.buffers = {
            0: self.input_buffer0,  # порт 0: ввод
            1: self.input_buffer1,  # порт 1: ввод
            2: self.output_buffer0,  # порт 2: вывод
            3: self.output_buffer1  # порт 3: вывод
        }
        self.alu_result = 0

    def write_in_memory(self):
        addr = self.stack[-2]
        val = self.stack[-1]
        if 0 <= addr < self.data_memory_size:
            self.data_memory[addr] = val
            print(f"Store {val} to address {addr}")
        else:
            raise Exception("Store address out of range")
        self.stack = self.stack[:-2]

    def read_from_memory(self):
        addr = self.stack[-1]
        self.stack = self.stack[:-1]
        if 0 <= addr < self.data_memory_size:
            val = self.data_memory[addr]
            print(f"Fetched {val} from address {addr}")
        else:
            raise Exception("Fetch address out of range")
        return val

    def flag_zero(self):
        flag = False
        if self.alu_result == 0:
            flag = True
        return flag


    def stack_to_a(self):
        self.a = self.stack[-1]
        self.stack = self.stack[:-1]

    def a_to_stack(self):
        self.stack.append(self.a)


    def alu(self, operand):
        value = 0
        self.stack_first = self.stack[-1]
        self.stack_second = self.stack[-2]
        if operand == "+":
            value = self.stack_first + self.stack_second
            self.stack = self.stack[:-2]
            value = self.check_carry(value)
        if operand == "-":
            value = self.stack_first - self.stack_second
            self.stack = self.stack[:-2]
            value = self.check_carry(value)
        if operand == "*":
            value = self.stack_first * self.stack_second
            self.stack = self.stack[:-2]
            value = self.check_carry(value)
        if operand == "/":
            if self.stack_first == 0:
                raise Exception("Division by zero")
            value = self.stack_first // self.stack_second
            self.stack = self.stack[:-2]
            value = self.check_carry(value)
        if operand == "~":
            value = ~self.stack_first
            self.stack = self.stack[:-1]
        if operand == "%":
            value = self.stack_first % self.stack_second
            self.stack = self.stack[:-2]
        if operand == "&":
            value = self.stack_first & self.stack_second
            self.stack = self.stack[:-2]
        if operand == "|":
            value = self.stack_first | self.stack_second
            self.stack = self.stack[:-2]
        if operand == "^":
            value = self.stack_first ^ self.stack_second
            self.stack = self.stack[:-2]
        if operand == "--":
            value = -self.stack_first
            value = self.check_carry(value)
            self.stack = self.stack[:-1]
        if operand == "==":
            value = int(self.stack_first == self.stack_second)
            self.stack = self.stack[:-2]
        if operand == ">":
            value = int(self.stack_first > self.stack_second)
            self.stack = self.stack[:-2]
        if operand == "<":
            value = int(self.stack_first < self.stack_second)
            self.stack = self.stack[:-2]
        self.alu_result = value

    def check_carry(self, value):
        # надо, чтобы привести к 32-битному знаковому числу
        if value < self.INT32_MIN or value > self.INT32_MAX:
            self.carry = 1
            value -= 2 ** 31
        else:
            self.carry = 0
        return value

    def stack_push(self, value):
        self.stack.append(value)

    def stack_pop(self):
        self.stack = self.stack[:-1]

    def push_return_stack(self):
        self.return_stack.append(self.program_counter)

    def pop_return_stack(self):
        self.a = self.return_stack[-1]
        self.return_stack = self.return_stack[:-1]

    def stack_to_pc(self):
        self.program_counter = self.a

    def get_key_from_input(self, port):
        if self.buffers[port]:
            ch = self.buffers[port].pop(0)
            self.a = ord(ch)
            print(f"Read char '{ch}' (code {ord(ch)})")
        else:
            self.a = 0
            print("Input buffer empty")

    def load_alu_value(self):
        self.alu_result = self.stack[-1]
        self.stack = self.stack[:-1]

    def send_char_to_output(self, port):
        if self.stack[-1] < 32:
            value = str(self.stack[-1])
        elif self.stack[-1] > 125:
            value = str(self.stack[-1])
        else:
            value = chr(self.stack[-1])
        self.buffers[port].append(value)
        print(f"Output char '{value}'")
        self.stack = self.stack[:-1]

    def save_to_return_stack(self):
        self.return_stack.append(self.stack[-1])
        self.stack = self.stack[:-1]
        print(self.return_stack)

    def return_stack_to_stack(self):
        self.stack.append(self.return_stack[-1])
        self.return_stack = self.return_stack[:-1]

    def save_alu_result(self):
        self.stack.append(self.alu_result)


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
        self.exit_out = ""
        self.next_command = False

    def tick(self):
        """Продвинуть модельное время процессора вперёд на один такт."""
        self._tick += 1

    def get_tick(self):
        return self._tick

    def new_input_index(self):
        self.input_index += 1

    def process_next_command(self):
        if self.halted:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            print(f"Tick: {self._tick}, "
                  f"PC: {self.data_path.program_counter}, "
                  f"Stack: [{self.data_path.stack[-1]}, {self.data_path.stack[-2]}], "
                  f"Input: {self.data_path.input_buffer0}, "
                  f"Output: {self.data_path.output_buffer0}, "
                  f"a: {self.data_path.a}, "
                  f"b: {self.data_path.return_stack}, "
                  f"dump: {self.data_path.data_memory[self.data_path.code_len:self.data_path.code_len + 50]}, ")
            raise StopIteration()

        # if self.data_path.program_counter >= self.data_path.program_memory_size:
        #    raise StopIteration()

        instr = self.data_path.data_memory[self.data_path.program_counter]
        if instr == "0":
            while instr == "0":
                self.data_path.program_counter += 1
                instr = self.data_path.data_memory[self.data_path.program_counter]
        opcode = instr["opcode"]
        # print(opcode)
        self.mpc = mapping.get(opcode, [])
        # print(self.mpc)
        prev_mpc = self.mpc
        mc = mp[prev_mpc]
        mc(self, instr)
        self.tick()

        while prev_mpc != self.mpc and (not self.next_command):
            prev_mpc = self.mpc
            mc = mp[self.mpc]
            mc(self, instr)
            self.tick()

        if not self.halted and opcode not in (Opcode.JUMP, Opcode.HALT, Opcode.CALL):
            self.next_command = False
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
        self.data_path.a = self.data_path.stack[-1]
        self.data_path.stack = self.data_path.stack[:-1]
        self.mpc += 1
        #self.rep_swap_dup = True

    # SWAP: меняет местами верхние два элемента стека
    def micro_swap(self, instr):
        print(f"[tick {self._tick}] SWAP")
        self.mpc += 1
        #self.rep_swap_dup = True

    # ADD
    def micro_add(self, instr):
        print(f"[tick {self._tick}] ADD")
        self.data_path.alu("+")
        self.mpc += 1

    # SUB
    def micro_sub(self, instr):
        print(f"[tick {self._tick}] SUB")
        self.data_path.alu("-")
        self.mpc += 1

    # MUL
    def micro_mul(self, instr):
        print(f"[tick {self._tick}] MUL")
        self.data_path.alu("*")
        self.mpc += 1

    # DIV
    def micro_div(self, instr):
        print(f"[tick {self._tick}] DIV")
        self.data_path.alu("/")
        self.mpc += 1

    # MOD
    def micro_mod(self, instr):
        print(f"[tick {self._tick}] MOD")
        self.data_path.alu("%")
        self.mpc += 1

    # NEGATE
    def micro_negate(self, instr):
        print(f"[tick {self._tick}] NEGATE")
        self.data_path.alu("--")
        self.mpc += 1

    # EQUAL (=)
    def micro_equal(self, instr):
        print(f"[tick {self._tick}] EQUAL")
        self.data_path.alu("==")
        self.mpc += 1

    # LESS (<)
    def micro_less(self, instr):
        print(f"[tick {self._tick}] LESS")
        self.data_path.alu("<")
        self.mpc += 1

    # GREATER (>)
    def micro_greater(self, instr):
        print(f"[tick {self._tick}] GREATER")
        self.data_path.alu(">")
        self.mpc += 1

    # AND
    def micro_and(self, instr):
        print(f"[tick {self._tick}] AND")
        self.data_path.alu("&")
        self.mpc += 1

    # OR
    def micro_or(self, instr):
        print(f"[tick {self._tick}] OR")
        self.data_path.alu("|")
        self.mpc += 1

    # XOR
    def micro_xor(self, instr):
        print(f"[tick {self._tick}] XOR")
        self.data_path.alu("^")
        self.mpc += 1

    # INVERT
    def micro_invert(self, instr):
        print(f"[tick {self._tick}] INVERT")
        self.data_path.alu("~")
        self.mpc += 1

    # IF (условный переход, реализуем как простой переход, если acc != 0)
    def micro_if_1(self, instr):
        print(f"[tick {self._tick}] IF - проверка условия")
        self.data_path.load_alu_value()
        self.mpc += 1
        #print("tos:", self.data_path.tos)

    def micro_if_2(self, instr):
        addr = instr["arg"]
        if self.data_path.flag_zero():
            self.data_path.program_counter = addr - 1
            print(f"[tick {self._tick}] IF - переход на {addr}")
        else:
            print(f"[tick {self._tick}] IF - переход не требуется (не ноль)")

    # STORE - записать в память по адресу в stack_second значение из stack_first
    def micro_store(self, instr):
        print(f"[tick {self._tick}] STORE")
        self.data_path.write_in_memory()

    # FETCH - загрузить в стек значение из памяти по адресу stack_first
    def micro_fetch(self, instr):
        print(f"[tick {self._tick}] FETCH")
        self.data_path.a = self.data_path.read_from_memory()
        self.mpc += 1

    # KEY - получить символ из входного буфера
    def micro_key(self, instr):
        print(f"[tick {self._tick}] KEY")
        port = instr["arg"]
        if port in self.data_path.buffers and (port == 0 or port == 1):
            self.data_path.get_key_from_input(port)
        else:
            raise ValueError(f"Неизвестный порт для чтения: {port}")
        self.mpc += 1

    # HALT
    def micro_halt(self, instr):
        print(f"[tick {self._tick}] HALT")
        self.halted = True

    # LIT - загрузить литерал из инструкции
    def micro_lit_1(self, instr):
        print(f"[tick {self._tick}] LIT - подготовка")
        self.mpc += 1

    def micro_lit_2(self, instr):
        print(f"[tick {self._tick}] LIT - загрузка значения {instr['arg']}")
        self.data_path.stack_push(instr["arg"])

    # EMIT - выводить символ из stack_first
    def micro_emit(self, instr):
        print(f"[tick {self._tick}] EMIT")
        port = instr["arg"]
        if port in self.data_path.buffers and (port == 2 or port == 3):
            self.data_path.send_char_to_output(port)
        else:
            raise ValueError(f"Неизвестный порт для записи: {port}")

    def save_comeback_adr(self, instr):
        print(f"[tick {self._tick}] COMEBACK ADR")
        self.data_path.push_return_stack()
        self.mpc += 1

    # JUMP - перейти на адрес, заданный в аргументе инструкции
    def micro_jump(self, instr):
        print(f"[tick {self._tick}] JUMP")
        target = instr.get("arg", 0)
        print(f"Jump to {target}")
        self.data_path.program_counter = target


    def micro_stack_to_a(self, instr):
        print(f"[tick {self._tick}] FIRST_STACK -> A")
        self.data_path.stack_to_a()
        self.mpc += 1

    def micro_a_to_stack(self, instr):
        print(f"[tick {self._tick}] A -> STACK")
        self.data_path.a_to_stack()
        self.mpc += 1


    def micro_ret(self, instr):
        # print(f"[tick {self._tick}] RET")
        self.data_path.pop_return_stack()
        self.data_path.stack_to_pc()

    def micro_carry(self, instr):
        print(f"[tick {self._tick}] CARRY")
        self.data_path.stack_push(self.data_path.carry)

    def micro_stack_2_ret_stack(self, instr):
        self.data_path.save_to_return_stack()
        self.mpc += 1

    def micro_ret_stack_2_stack(self, instr):
        self.data_path.return_stack_to_stack()
        self.mpc += 1

    def micro_next_command(self, instr):
        self.next_command = True
        return

    def micro_alu_2_stack(self, instr):
        self.data_path.save_alu_result()
        self.mpc += 1

    def __str__(self):
        return (f"Tick: {self._tick}, "
                f"PC: {self.data_path.program_counter}, "
                f"Stack: [{self.data_path.stack[-1]}, {self.data_path.stack[-2]}], "
                f"Input: {self.data_path.input_buffer0}, "
                f"Output: {self.data_path.output_buffer0}, "
                f"a: {self.data_path.a}, "
                f"b: {self.data_path.return_stack}, "
                f"dump: {self.data_path.data_memory[self.data_path.code_len - 1:self.data_path.code_len + 50]}, ")


def simulation(code, code_len, input_tokens, data_memory_size, limit):
    data_path = Datapath(data_memory_size, input_tokens, code, code_len)
    control_unit = ControlUnit(data_path)

    logging.debug("%s", control_unit)
    try:
        while control_unit.get_tick() < limit:
            control_unit.process_next_command()
            logging.debug("%s", control_unit)
    except EOFError:
        logging.warning("Input buffer is empty!")
    except StopIteration:
        pass

    if control_unit.get_tick() >= limit:
        logging.warning("Tick limit exceeded!")

    return "".join(data_path.output_buffer0), control_unit.get_tick()


# Массив микрокода
mp = [
    ControlUnit.micro_swap,                 # 0 swap
    ControlUnit.micro_stack_2_ret_stack,    # 1
    ControlUnit.micro_stack_to_a,           # 2
    ControlUnit.micro_ret_stack_2_stack,    # 3
    ControlUnit.micro_a_to_stack,           # 4
    ControlUnit.micro_next_command,         # 5
    ControlUnit.micro_add,                  # 6 +
    ControlUnit.micro_alu_2_stack,          # 7
    ControlUnit.micro_next_command,         # 8
    ControlUnit.micro_sub,                  # 9 -
    ControlUnit.micro_alu_2_stack,          # 10
    ControlUnit.micro_next_command,         # 11
    ControlUnit.micro_mul,                  # 12 *
    ControlUnit.micro_alu_2_stack,          # 13
    ControlUnit.micro_next_command,         # 14
    ControlUnit.micro_div,                  # 15 //
    ControlUnit.micro_alu_2_stack,          # 16
    ControlUnit.micro_next_command,         # 17
    ControlUnit.micro_mod,                  # 18 %
    ControlUnit.micro_alu_2_stack,          # 19
    ControlUnit.micro_next_command,         # 20
    ControlUnit.micro_negate,               # 21 --
    ControlUnit.micro_alu_2_stack,          # 22
    ControlUnit.micro_next_command,         # 23
    ControlUnit.micro_equal,                # 24 ==
    ControlUnit.micro_alu_2_stack,          # 25
    ControlUnit.micro_next_command,         # 26
    ControlUnit.micro_less,                 # 27 <
    ControlUnit.micro_alu_2_stack,          # 28
    ControlUnit.micro_next_command,         # 29
    ControlUnit.micro_greater,              # 30 >
    ControlUnit.micro_alu_2_stack,          # 31
    ControlUnit.micro_next_command,         # 32
    ControlUnit.micro_and,                  # 33 and
    ControlUnit.micro_alu_2_stack,          # 34
    ControlUnit.micro_next_command,         # 35
    ControlUnit.micro_or,                   # 36 or
    ControlUnit.micro_alu_2_stack,          # 37
    ControlUnit.micro_next_command,         # 38
    ControlUnit.micro_xor,                  # 39 xor
    ControlUnit.micro_alu_2_stack,          # 40
    ControlUnit.micro_next_command,         # 41
    ControlUnit.micro_invert,               # 42 invert
    ControlUnit.micro_alu_2_stack,          # 43
    ControlUnit.micro_next_command,         # 44
    ControlUnit.micro_if_1,                 # 45 if
    ControlUnit.micro_if_2,                 # 46
    ControlUnit.micro_next_command,         # 47
    ControlUnit.micro_fetch,                # 48 @
    ControlUnit.micro_a_to_stack,           # 49
    ControlUnit.micro_next_command,         # 50
    ControlUnit.micro_key,                  # 51 in
    ControlUnit.micro_a_to_stack,           # 52
    ControlUnit.micro_next_command,         # 53
    ControlUnit.micro_store,                # 54 !
    ControlUnit.micro_lit_1,                # 55 lit
    ControlUnit.micro_lit_2,                # 56
    ControlUnit.save_comeback_adr,          # 57 call
    ControlUnit.micro_jump,                 # 58 jump
    ControlUnit.micro_ret,                  # 59 ret
    ControlUnit.micro_drop,                 # 60 drop
    ControlUnit.micro_dup,                  # 61 dup
    ControlUnit.micro_a_to_stack,           # 62
    ControlUnit.micro_a_to_stack,           # 63
    ControlUnit.micro_next_command,         # 64
    ControlUnit.micro_emit,                 # 65 out
    ControlUnit.micro_carry,                # 66 c
    ControlUnit.micro_halt                  # 67 halt
]

mapping = {
    Opcode.SWAP: 0,
    Opcode.ADD: 6,
    Opcode.SUB: 9,
    Opcode.MUL: 12,
    Opcode.DIV: 15,
    Opcode.MOD: 18,
    Opcode.NEGATE: 21,
    Opcode.EQUAL: 24,
    Opcode.LESS: 27,
    Opcode.GREATER: 30,
    Opcode.AND: 33,
    Opcode.OR: 36,
    Opcode.XOR: 39,
    Opcode.INVERT: 42,
    Opcode.IF: 45,
    Opcode.FETCH: 48,
    Opcode.IN: 51,
    Opcode.STORE: 54,
    Opcode.LIT: 55,
    Opcode.CALL: 57,
    Opcode.JUMP: 58,
    Opcode.RET: 59,
    Opcode.DROP: 60,
    Opcode.DUP: 61,
    Opcode.OUT: 65,
    Opcode.CARRY: 66,
    Opcode.HALT: 67
}


def main(code, file_input, out):
    if out:
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")
        logging.getLogger().setLevel(logging.CRITICAL + 1)
    with open(code, "rb") as file:
        text_code = file.read()
    binary_code = bytearray(text_code)
    code, code_len = bin_to_opcode(binary_code)
    print(code)
    print(code_len, code[code_len - 1:])
    with open(file_input, encoding="utf-8") as file:
        input_text = file.read()
        input_tokens = list(input_text)

    output, ticks = simulation(code, code_len, input_tokens, data_memory_size=3000, limit=200000000)
    print(output)
    print("ticks:", ticks)


original_stdout = sys.stdout
original_stderr = sys.stderr
if __name__ == "__main__":
    quiet = "--quiet" in sys.argv
    if quiet:
        sys.argv.remove("--quiet")
        assert len(sys.argv) == 3, "Usage: machine.py <code_file> <input_file>"
        _, code_file, input_file = sys.argv
        main(code_file, input_file, True)
    else:
        logging.getLogger().setLevel(logging.DEBUG)
        assert len(sys.argv) == 3, "Usage: machine.py <code_file> <input_file>"
        _, code_file, input_file = sys.argv
        main(code_file, input_file, False)
