import logging
import sys
from isa import Opcode, from_bytes,opcode_to_binary

class Datapath:
    stack_first = None # Верхняя ячейка стека
    stack_second = None # Нижняя ячейка стека
    input_buffer = None # Буфер входных данных. Инициализируется входными данными конструктора.
    output_buffer = None # Буфер выходных данных.
    data_memory_size = None # Размер памяти данных.
    data_memory = None # Память данных. Инициализируется нулевыми значениями.
    data_address = None # Адрес в памяти данных. Инициализируется нулём.

    def __init__(self, data_memory_size, input_buffer):
        assert data_memory_size > 0, "Data_memory size should be non-zero"
        self.data_memory_size = data_memory_size
        self.data_memory = [0] * data_memory_size
        self.data_address = 0
        self.stack_first = 0
        self.stack_second = 0
        self.input_buffer = input_buffer
        self.output_buffer = []


class ControlUnit:
    program = None # Память команд.
    program_counter = None # Счётчик команд. Инициализируется нулём.
    data_path = None # Блок обработки данных.
    _tick = None # Текущее модельное время процессора (в тактах). Инициализируется нулём.

    def __init__(self, program, data_path):
        self.program = program
        self.program_counter = 0
        self.data_path = data_path
        self._tick = 0
        self.step = 0

    def tick(self):
        """Продвинуть модельное время процессора вперёд на один такт."""
        self._tick += 1

    def get_tick(self):
        return self._tick

    def signal_latch_program_counter(self, sel_next):
        """Защёлкнуть новое значение счётчика команд.

        Если `sel_next` равен `True`, то счётчик будет увеличен на единицу,
        иначе -- будет установлен в значение аргумента текущей инструкции.
        """
        if sel_next:
            self.program_counter += 1
        else:
            instr = self.program[self.program_counter]
            assert "arg" in instr, "internal error"
            self.program_counter = instr["arg"]

    def process_next_tick(self):  # noqa: C901 # код имеет хорошо структурирован, по этому не проблема.
        """Основной цикл процессора. Декодирует и выполняет инструкцию.

        Обработка инструкции:

        1. Проверить `Opcode`.

        2. Вызвать методы, имитирующие необходимые управляющие сигналы.

        3. Продвинуть модельное время вперёд на один такт (`tick`).

        4. (если необходимо) повторить шаги 2-3.

        5. Перейти к следующей инструкции.

        Обработка функций управления потоком исполнения вынесена в
        `decode_and_execute_control_flow_instruction`.
        """
        instr = self.program[self.program_counter]
        opcode = instr["opcode"]

        if opcode is Opcode.HALT:
            raise StopIteration()

        if opcode is Opcode.IF:
            addr = instr["arg"]
            self.program_counter = addr
            self.step = 0
            self.tick()
            return

        if opcode is Opcode.DROP:
            # Удаляем верхний элемент стека
            self.data_path.stack_first = 0x0
            self.tick()
            self.signal_latch_program_counter(sel_next=True)
            return

        if opcode is Opcode.DUP:
            # Дублируем верхний элемент стека
            self.data_path.stack_second = self.data_path.stack_first
            self.tick()
            self.signal_latch_program_counter(sel_next=True)
            return

        if opcode is Opcode.SWAP:
            # Меняем верхний и нижний значения стека местами
            self.data_path.stack_first, self.data_path.stack_second = self.data_path.stack_second, self.data_path.stack_first
            self.tick()
            self.signal_latch_program_counter(sel_next=True)
            return

        if opcode is Opcode.ADD:
            # Складываем значения стека
            self.data_path.stack_first, self.data_path.stack_second = self.data_path.stack_first + self.data_path.stack_second, self.data_path.stack_first
            self.tick()
            self.signal_latch_program_counter(sel_next=True)
            return

        if opcode is Opcode.SUB:
            # Вычитаем значения стека
            self.data_path.stack_first, self.data_path.stack_second = self.data_path.stack_first - self.data_path.stack_second, self.data_path.stack_first
            self.tick()
            self.signal_latch_program_counter(sel_next=True)
            return

        if opcode is Opcode.MUL:
            # Умножаем значения стека
            self.data_path.stack_first, self.data_path.stack_second = self.data_path.stack_first * self.data_path.stack_second, self.data_path.stack_first
            self.tick()
            self.signal_latch_program_counter(sel_next=True)
            return

        if opcode is Opcode.DIV:
            # Делим значения стека
            self.data_path.stack_first, self.data_path.stack_second = self.data_path.stack_first / self.data_path.stack_second, self.data_path.stack_first
            self.tick()
            self.signal_latch_program_counter(sel_next=True)
            return

        if opcode is Opcode.MOD:
            # Находим остаток от деления второго элемента на первый
            self.data_path.stack_first, self.data_path.stack_second = self.data_path.stack_second % self.data_path.stack_first, self.data_path.stack_first
            self.tick()
            self.signal_latch_program_counter(sel_next=True)
            return

        if opcode is Opcode.NEGATE:
            # Пока заглущка
            return

        if opcode is Opcode.EQUAL:
            # Проверка на равенство верхнего и нижнего значения стека
            if self.data_path.stack_first == self.data_path.stack_second:
                self.data_path.stack_first = 0x1
            else:
                self.data_path.stack_second = 0x0
            self.tick()
            self.signal_latch_program_counter(sel_next=True)
            return

        if opcode is Opcode.LESS:
            # Проверка на то, больше ли верхнее значение стека нижнего
            if self.data_path.stack_first > self.data_path.stack_second:
                self.data_path.stack_first = 0x1
            else:
                self.data_path.stack_second = 0x0
            self.tick()
            self.signal_latch_program_counter(sel_next=True)
            return

        if opcode is Opcode.GREATER:
            # Проверка на то, больше ли нижнее значение стека верхнего
            if self.data_path.stack_first > self.data_path.stack_second:
                self.data_path.stack_first = 0x1
            else:
                self.data_path.stack_second = 0x0
            self.tick()
            self.signal_latch_program_counter(sel_next=True)
            return

        if opcode is Opcode.AND:
            # Побитовое И
            self.data_path.stack_first, self.data_path.stack_second = self.data_path.stack_second & self.data_path.stack_first, self.data_path.stack_first
            self.tick()
            self.signal_latch_program_counter(sel_next=True)
            return

        if opcode is Opcode.OR:
            # Побитовое ИЛИ
            self.data_path.stack_first, self.data_path.stack_second = self.data_path.stack_second | self.data_path.stack_first, self.data_path.stack_first
            self.tick()
            self.signal_latch_program_counter(sel_next=True)
            return

        if opcode is Opcode.XOR:
            # Побитовое ИСКЛЮЧАЮЩЕЕ ИЛИ
            self.data_path.stack_first, self.data_path.stack_second = self.data_path.stack_second ^ self.data_path.stack_first, self.data_path.stack_first
            self.tick()
            self.signal_latch_program_counter(sel_next=True)
            return

        if opcode is Opcode.INVERT:
            # Побитовое НЕ
            self.data_path.stack_first, self.data_path.stack_second = ~self.data_path.stack_second, self.data_path.stack_first
            self.tick()
            self.signal_latch_program_counter(sel_next=True)
            return

        if opcode is Opcode.STORE:
            # Сохранение в память
            addr = self.data_path.stack_second
            value = self.data_path.stack_first
            assert 0 <= addr < self.data_path.data_memory_size, "Invalid memory address"
            self.data_path.data_memory[addr] = value
            self.data_path.stack_first = 0
            self.data_path.stack_second = 0
            self.tick()
            self.signal_latch_program_counter(sel_next=True)
            return

        if opcode is Opcode.FETCH:
            # Загрузка из памяти
            addr = self.data_path.stack_first
            assert 0 <= addr < self.data_path.data_memory_size, "Invalid memory address"
            value = self.data_path.data_memory[addr]
            self.data_path.stack_second = addr
            self.data_path.stack_first = value
            self.tick()
            self.signal_latch_program_counter(sel_next=True)
            return

        if opcode is Opcode.KEY:
            # Считать символ с клавиатуры
            if not self.data_path.input_buffer:
                raise RuntimeError("Input buffer is empty")
            char = self.data_path.input_buffer[0]
            self.data_path.input_buffer = self.data_path.input_buffer[1:]
            self.data_path.stack_second = self.data_path.stack_first
            self.data_path.stack_first = ord(char)
            self.tick()
            self.signal_latch_program_counter(sel_next=True)
            return

        if opcode is Opcode.LIT:
            # Прямая загрузка в вершину стека
            vaule = instr["arg"]
            self.data_path.stack_first, self.data_path.stack_second = vaule, self.data_path.stack_first
            self.tick()
            self.signal_latch_program_counter(sel_next=True)
            return


def __repr__(self):
    state_repr = "TICK: {:3} PC: {:3} ADDR: {:3} MEM[ADDR]: {:3} STACK: [{}, {}]".format(
        self._tick,
        self.program_counter,
        self.data_path.data_address,
        self.data_path.data_memory[self.data_path.data_address],
        self.data_path.stack_first,
        self.data_path.stack_second,
    )

    instr = self.program[self.program_counter]
    opcode = instr["opcode"]
    instr_repr = str(opcode)
    if "arg" in instr:
        instr_repr += " {}".format(instr["arg"])

    instr_hex = f"{opcode_to_binary[opcode] << 28 | (instr.get('arg', 0) & 0x0FFFFFFF):08X}"

    return "{} \t{} [{}]".format(state_repr, instr_repr, instr_hex)


def simulation(code, input_tokens, data_memory_size, limit):
    data_path = Datapath(data_memory_size, input_tokens)
    control_unit = ControlUnit(code, data_path)

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


def main(code_file, input_file):
    with open(code_file, "rb") as file:
        binary_code = file.read()
    code = from_bytes(binary_code)

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
