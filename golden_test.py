import pytest
import contextlib
import io
import logging
import os
import tempfile
import machine
import translator
MAX_LOG = 400000000




@pytest.mark.golden_test("golden/hello_world.yml")
def test_translator_and_machine_hello_world(golden, caplog):
    run_test(golden, caplog, True)

@pytest.mark.golden_test("golden/hello_user_name0.yml")
def test_translator_and_machine_hello_user_name0(golden, caplog):
    run_test(golden, caplog, True)

@pytest.mark.golden_test("golden/hello_user_name1.yml")
def test_translator_and_machine_hello_user_name1(golden, caplog):
    run_test(golden, caplog, True)

@pytest.mark.golden_test("golden/cat.yml")
def test_translator_and_machine_cat(golden, caplog):
    run_test(golden, caplog, True)

@pytest.mark.golden_test("golden/sort.yml")
def test_translator_and_machine_sort(golden, caplog):
    run_test(golden, caplog, True)

@pytest.mark.golden_test("golden/carry_check.yml")
def test_translator_and_machine_carry_check(golden, caplog):
    run_test(golden, caplog, True)

@pytest.mark.golden_test("golden/prob.yml")
def test_translator_and_machine_prob1(golden, caplog):
    run_test(golden, caplog, False)

def run_test(golden, caplog, need_ticks):
    caplog.set_level(logging.DEBUG)

    with tempfile.TemporaryDirectory() as tmpdirname:
        source = os.path.join(tmpdirname, "in_code")
        input_stream = os.path.join(tmpdirname, "input_stream")
        target = os.path.join(tmpdirname, "target.bin")
        target_hex = os.path.join(tmpdirname, "target.bin.hex")

        with open(source, "w", encoding="utf-8") as file:
            file.write(golden["in_code"])
        with open(input_stream, "w", encoding="utf-8") as file:
            file.write(golden["in_stdin"])

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            translator.main(source, target)
            print("============================================================")
            machine.main(target_hex, input_stream, not need_ticks)

        with open(target_hex, encoding="utf-8") as file:
            code_hex = file.read()
        if need_ticks:
            assert code_hex == golden.out["out_code_hex"]
            assert stdout.getvalue() == golden.out["out_stdout"]
            assert caplog.text[:MAX_LOG] + "EOF" == golden.out["out_log"]
