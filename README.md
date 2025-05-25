# csa-lab4
# Laboratory work № 4. Experiment
- Амузинский Артем Андреевич, P3206
- Ваиант: `alg -> forth | stack | neum | mc | tick | binary | stream | port | pstr | prob1 | cache`
- Расшифровка варианта:
  - `forth`: forth-like stack-based syntax with Reverse Polish Notation (RPN)
  - `stack`: stack-based CPU architecture
  - `neum`: Von Neumann architecture
  - `mc`: microcoded control unit
  - `tick`: cycle-accurate simulation 
  - `binary`: true binary machine code
  - `stream`: stream based I/O
  - `port`: port-mapped I/O
  - `pstr`: Length-prefixed (Pascal string)
  - `prob1`: Find the largest palindrome made from the product of two 3-digit numbers.

**DROP** – Удаляет верхний элемент стека. <br>
**DUP** – Дублирует верхний элемент стека. <br>
**SWAP** – Меняет местами два верхних элемента стека. <br>
**\+** – Складывает два верхних элемента стека. <br>
**\-** – Вычитает верхний элемент из второго. <br>
**\*** – Умножает два верхних элемента. <br>
**/** – Делит второй элемент на верхний. <br>
**MOD** – Остаток от деления второго элемента на верхний. <br>
**NEGATE** – Инвертирует знак верхнего элемента. <br>
**=** – Проверяет равенство двух верхних элементов, кладет -1 (истина) или 0 (ложь).<br>
**\<** – Проверяет, меньше ли второй элемент, чем верхний.<br>
**\>** – Проверяет, больше ли второй элемент, чем верхний.<br>
**AND** – Побитовая операция И для двух верхних элементов.<br>
**OR** – Побитовая операция ИЛИ для двух верхних элементов.<br>
**XOR** – Побитовая операция Исключающее ИЛИ.<br>
**INVERT** – Инвертирует все биты верхнего элемента.<br>
**IF** – Условное выполнение: если верхний элемент стека не 0, выполняет код между IF и THEN.<br>
**!** – Записывает значение во вторую ячейку памяти (addr value !).<br>
**@** – Читает значение из памяти (addr @).<br>
**KEY** – Считывает один символ с клавиатуры и кладет его код в стек.<br>
**halt** – остановка тактового генератора.<br>
**lit** – Загрузка литерала в вершину стека.<br>
**emit** – Загрузка вершины стека в буфер вывода.<br>
**jump** – Переход на метку.<br>
**call** – Вызов процедуры.<br>
**ret** – Возвращение из процедуры.<br>
## Схемы
https://drive.google.com/file/d/1yH4xpJZjwfba7quabQ0sjdoASbY9od4I/view?usp=sharing
```ebnf
<program> ::= <line>*

<line> ::= <label> <comment>? "\n"
        | <instr> <comment>? "\n"
        | <comment> "\n"

<label> ::= <label_name> ":"

<instr> ::= <op0>
         | <op1> " " <label_name>
         | <op1> " " <positive_integer>

<op0> ::= "drop"
       | "dup"
       | "swap"
       | "+"
       | "-"
       | "*"
       | "/"
       | "mod"
       | "negate"
       | "="
       | "<"
       | ">"
       | "and"
       | "or"
       | "xor"
       | "invert"
       | "if"
       | "exit"
       | "!"
       | "@"
       | "key"
       | "halt"
       | "emit"
       | "ret"

<op1> ::= "lit"
       | "call"
       | "jump"

<positive_integer> ::= [0-9]+

<lowercase_letter> ::= [a-z]
<uppercase_letter> ::= [A-Z]
<letter> ::= <lowercase_letter> | <uppercase_letter>
<digit> ::= [0-9]
<integer> ::= "-"? <digit>+

<letter_or_digit> ::= <letter> | <digit>
<letter_or_digit_or_underscore> ::= <letter_or_digit> | "_"

<label_name> ::= <letter> <letter_or_digit_or_underscore>*

<comment> ::= " "* ";" " "* <comment_text>?
<comment_text> ::= <letter_or_digit_or_underscore> ( " " <letter_or_digit_or_underscore> )*

```
