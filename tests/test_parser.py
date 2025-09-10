from pr_analyzer.parser import parse_stack_trace


def test_parse_python_frame():
    trace = '  File "app/main.py", line 42, in handler\n    raise ValueError("oops")\n'
    frames = parse_stack_trace(trace)
    assert len(frames) == 1
    assert frames[0]["lang"] == "python"
    assert frames[0]["file"].endswith("app/main.py")


def test_parse_java_frame():
    trace = '    at com.example.MyClass.myMethod(MyClass.java:123)'
    frames = parse_stack_trace(trace)
    assert len(frames) == 1
    assert frames[0]["lang"] == "java"
    assert frames[0]["line"] == 123
