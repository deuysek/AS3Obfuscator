import re
import os
import time
import json
import random

config = {
    "obfuscate_numbers": True,
    "obfuscate_access_chains": True,
    "addJunkCode": True,
    "junkCodeLevel":3,
    "ignoreTrace": True,
    "convertToES4": False,
    "input":"./Decrypter.as",
    "output":"./Obfuscator.as",
}

lines = []
import_code = []
obfuscated = []
start_time = 0

_is_in_package = False
_last_enter_package = 0
_is_in_class = False
_last_enter_class = 0
_is_in_function = False
_last_enter_function = 0
_brace_count = 0
_just_in = False

def get_random_string(length = 6):
    pre = random.choice("abcdefghijklmnopqrstuvwxyz") + random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    end = random.choice("abcdefghijklmnopqrstuvwxyz") + random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    return pre + "".join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=length)) + end

def get_random_access_chain(depth = 5):
    code = ""
    while depth:
        depth -= 1
        code += get_random_string(random.randint(1,5)) + "."
    return code[:-1]

def get_random_operator():
    return random.choice(["+","-","*","/","%","&","|","^","<<",">>"])

def get_random_formular():
    """
    59966>>59108%63435>>40411<<5593<<15953
    """
    code = ""
    code += str(random.randint(50,65535))
    for i in range(random.randint(15,20)):
        code += get_random_operator() + str(random.randint(50,65535))
    return code

def get_randomm_statement(is_var = True,is_ns_var = False, is_access_chain = True):
    var = [
        "public var " + get_random_string(random.randint(3,5)) + ":Number = " + get_random_formular() + ";",
        "private var " + get_random_string(random.randint(3,5)) + ":Number = " + get_random_formular() + ";",
        "public var " + get_random_string(random.randint(3,5)) + ":String = \"" + get_random_string() + "\";",
        "private var " + get_random_string(random.randint(3,5)) + ":String = \"" + get_random_string() + "\";",
        "public var " + get_random_string(random.randint(3,5)) + ":Boolean = Boolean(\"" + get_random_string() + "\");",
        "private var " + get_random_string(random.randint(3,5)) + ":Boolean = Boolean(\"" + get_random_string() + "\");",
    ]
    if not is_ns_var:
        var = [i[i.find(" var") + 1:] for i in var]
    acc = [
        get_random_access_chain() + " = " + get_random_access_chain() + ";",
        get_random_access_chain() + " = " + get_random_formular() + ";",
        get_random_access_chain() + " = " + get_random_string(random.randint(1,3)) +";",
        get_random_access_chain() + " == " + get_random_access_chain() + ";",
        get_random_access_chain() + " == " + get_random_formular() + ";",
        get_random_access_chain() + " == " + get_random_string(random.randint(1,3)) +";",
    ]
    if not is_var: var = []
    if not is_access_chain: acc = []
    if len(var + acc) == 0: return ""
    return random.choice(var + acc) + "\n"

def wrap_in_func(code,is_ns:True):
    ns = [
        "public ",
        "private ",
        "internal ",
    ]
    return (random.choice(ns) if is_ns else "") + "function " + get_random_string(5) + "():void\n{\n" + code + "}\n"

def wrap_in_class(code):
    return "class " + get_random_string(5) + "{\n" + code + "}\n"

def get_random_block():
    code = [
        "try{" + "".join([get_randomm_statement(is_ns_var=False) for i in range(5)]) + "}" + "catch(e)" + "{" + "".join([get_randomm_statement(is_ns_var=False) for i in range(5)]) + "}"
        f"while ({get_random_access_chain(3)} == {get_random_access_chain(5)})" + "{" + "".join([get_randomm_statement(is_ns_var=False) for i in range(5)]) + "}\n",
        f"while ({get_random_access_chain(3)} == {get_random_formular()})" + "{" + "".join([get_randomm_statement(is_ns_var=False) for i in range(5)]) + "}\n",
        f"if ({get_random_access_chain(3)} == {get_random_access_chain(5)})" + "{" + "".join([get_randomm_statement(is_ns_var=False) for i in range(5)]) + "}\n",
        f"if ({get_random_access_chain(3)} == {get_random_formular()})" + "{" + "".join([get_randomm_statement(is_ns_var=False) for i in range(5)]) + "}\n",
    ]
    es4code = [
        f"for each(var {get_random_string(5)} in {get_random_string()})" + "{" + "".join([get_randomm_statement(is_ns_var=False) for i in range(5)]) + "}\n",
        f"for ({get_random_string(5)} in {get_random_string()})" + "{" + "".join([get_randomm_statement(is_ns_var=False) for i in range(5)]) + "}\n",
    ]
    return random.choice((code + es4code) if config["convertToES4"] else code)

def get_random_class():
    code = ""
    for i in range(random.randint(5,11)):
        code += get_randomm_statement(is_access_chain=False)
        code += wrap_in_func(get_random_block() + get_randomm_statement(),False)
    return wrap_in_class(code)

def get_random_function(is_ns):
    code = ""
    for i in range(random.randint(5,11)):
        code += get_randomm_statement(is_access_chain=False)
        code += wrap_in_func(get_random_block() + get_randomm_statement(),False)
    return wrap_in_func(code,is_ns=is_ns)

def is_in_package():
    return _is_in_package and _brace_count >= _last_enter_package and (not _is_in_function) and (not _is_in_class)

def is_in_class():
    return _is_in_class and _brace_count >= _last_enter_class and (not _is_in_function)

def is_in_function():
    return _is_in_function and _brace_count >= _last_enter_function

def check_syntax(code):
    code_str = str(code)
    is_pass = True
    is_pass &= code_str.count("\"") % 2 == 0
    is_pass &= code_str.count("\'") % 2 == 0
    is_pass &= code_str.count("{") == code_str.count("}")
    is_pass &= code_str.count("(") == code_str.count(")")
    return is_pass

def addJunkCode(code_list,is_add_class = True):
    garbage_att = [
        "var " + get_random_string(5) + "_" + str(random.randint(0, 65535)) + ":String = \"Dame__" + get_random_string() + "\";",
        "var " + get_random_string(5) + "_" + str(random.randint(0, 65535)) + ":String = \"Give UP__" + get_random_string() + "\";",
    ]
    garbage_func = [
        "private function " + get_random_string(5) + "_" + str(random.randint(0, 65535)) + r"():void{while(true){}function(){}for(i in {}){ba;ba;ba}}",
        "public function " + get_random_string(5) + "_" + str(random.randint(0, 65535)) + r"():void{}",
    ]
    garbage_class = [
        "public class " + get_random_string(5) + str(random.randint(0, 65535)) + r"{" + random.choice(garbage_att + garbage_func) + r"}",
        "private class " + get_random_string(5) + str(random.randint(0, 65535)) + r"{" + random.choice(garbage_att + garbage_func) + r"}",
        "internal class " + get_random_string(5) + str(random.randint(0, 65535)) + r"{" + random.choice(garbage_att + garbage_func) + r"}",
        "public final class " + get_random_string(5) + str(random.randint(0, 65535)) + r"{" + random.choice(garbage_att + garbage_func) + r"}",
        "private final class " + get_random_string(5) + str(random.randint(0, 65535)) + r"{" + random.choice(garbage_att + garbage_func) + r"}",
        "internal final class " + get_random_string(5) + str(random.randint(0, 65535)) + r"{" + random.choice(garbage_att + garbage_func) + r"}",
        "public dynamic class " + get_random_string(5) + str(random.randint(0, 65535)) + r"{" + random.choice(garbage_att + garbage_func) + r"}",
        "private dynamic class " + get_random_string(5) + str(random.randint(0, 65535)) + r"{" + random.choice(garbage_att + garbage_func) + r"}",
        "internal dynamic class " + get_random_string(5) + str(random.randint(0, 65535)) + r"{" + random.choice(garbage_att + garbage_func) + r"}",
    ]
    if not is_add_class:
        garbage_class = []
    pool = garbage_att + garbage_class if config["convertToES4"] else garbage_att + garbage_func + garbage_class
    tar_code = random.choice(pool)
    code_list.append(tar_code + "\n")

def enc_string(string):
    if string == "":
        return ""
    enc = ""
    # if len(string) > 20:
    #     return "String.fromCharCode(" + str(random.randint(0, 255)) + ")"
    #String.fromCharCode(123) + String.fromCharCode(123)
    for i in string:
        enc += "String.fromCharCode(" + str(enc_number(ord(i))) + ") + "
    if "String" in enc:
        return enc[:-3]
    
def enc_number(number):
    rand_key = random.randint(0, 65535)
    enc_num = number ^ rand_key
    return str(enc_num) + " ^ " + str(rand_key)


def process_number(match):
    if not config["obfuscate_numbers"]:
        return match.group(0)
    # 获取匹配到的数字
    num_str = match.group(0)
    # 将字符串转换为浮点数或整数
    num = float(num_str) if '.' in num_str else int(num_str)
    # 对数字进行处理，例如加100
    return str(enc_number(num))

def process_access_chain(match):
    if not config["obfuscate_access_chains"]:
        return match.group(0)
    # 获取匹配到的属性链
    access = match.group(0)[1:]
    # 对属性链进行处理，例如替换为随机字符串
    access = enc_string(access)
    return "[" + access + "]"

if __name__ == "__main__":
    print("Py AS3 Obfuscator (AS3 Eval Edition)\nby @Duskeye\n(=・ω・=)")

    with open("./config.json", "r", encoding="utf-8") as f:
        cg = json.load(f)
        f.close()

    for i in config.keys():
        if i in cg.keys():
            config[i] = cg[i]
    
    if config["junkCodeLevel"] > 5 and config["convertToES4"] == False:
        # print("添加过多混淆代码可能会导致AS3Eval编译时间过长, 尝试降低混淆级别或者开启ES4Eval")
        print("To many Obfuscates whill lead to long compile time for AS3Eval. Try to reduce the junk code level or enable ES4Eval")
        exit()

    print("File Path: " + os.path.abspath(config["input"]))
    if not os.path.isfile(config["input"]) or not os.path.exists(config["input"]):
        print("Invalid file path!")
    start_time = time.time()

    with open(config["input"], "r",encoding="utf-8") as f:
        if not check_syntax(f.read()):
            print("Invalid syntax!")
            exit()
        f.seek(0)
        lines = f.readlines()
        f.close()

    print("Obfuscating code...")
    for code in (lines):
        if "//" in code:
            continue
        if "trace" in code and config["ignoreTrace"]:
            continue
        _brace_count += code.count("{")
        if "package" in code:
            _is_in_package = True
            _last_enter_package = _brace_count + 1
            _just_in = True
        if "class" in code:
            _is_in_class = True
            _last_enter_class = _brace_count + 1
            _just_in = True
        if "function" in code:
            _is_in_function = True
            _last_enter_function = _brace_count + 1
            _just_in = True
        _brace_count -= code.count("}")
        if _just_in:
            _just_in = False
        else:
            if _brace_count < _last_enter_package and _is_in_package:
                _is_in_package = False
            if _brace_count < _last_enter_class and _is_in_class:
                _is_in_class = False
            if _brace_count < _last_enter_function and _is_in_function:
                _is_in_function = False
        if "import " in code:
            if config["convertToES4"]:
                nsName = get_random_string(1)
                code = "namespace " + nsName + " = \"" + code[code.index("import ") + 7 : code.rindex(".")] + "\"; use namespace " + nsName + ";\n"
                obfuscated.append(code)
                continue
            else:
                import_code.append(code)
                continue
        if "package" in code or "class" in code:
            obfuscated.append(code)
            continue

        pattern = r'\.(\w+)'
        string_pattern = r'("[^"]*"|\'[^\']*\')'
        strings = re.findall(string_pattern, code)
        placeholder = "<<<STRING>>>"
        # 将字符串替换为占位符
        code_no_strings = re.sub(string_pattern, placeholder, code)
        num_pattern = r'\b\d+(\.\d+)?\b'
        code_no_strings = re.sub(num_pattern, process_number, code_no_strings)

        code_no_strings = code_no_strings.replace("...","||||")
        # 2. 替换属性链的每一级
        # 匹配 .属性名，并替换为 ["属性名"]
        property_pattern = r'\.(\w+)'
        code = re.sub(property_pattern, process_access_chain, code_no_strings)
        code = code.replace("||||","...")

        # 3. 恢复原来的字符串内容
        if strings:
            for i in range(len(strings)):
                code = code.replace(placeholder, enc_string(strings[i]), 1)
        obfuscated.append(code)
        if is_in_class() and config["addJunkCode"]:
            for i in range(config["junkCodeLevel"]):
                pass
                obfuscated.append(get_randomm_statement(is_var=True,is_ns_var=False,is_access_chain=False))
                obfuscated.append(get_random_function(True))
    print("done")
    if config["addJunkCode"]:
        print("Adding junk code...")
        for i in range(config["junkCodeLevel"]):
            obfuscated.insert(0, get_random_class())
            obfuscated.insert(0, get_random_function(is_ns=not config["convertToES4"]))
            obfuscated.append(get_random_class())
            obfuscated.append(get_random_function(is_ns=not config["convertToES4"]))
        print("done")
    if len(import_code) > 0:
        obfuscated = import_code + obfuscated
    print("Time cost: " + str(time.time() - start_time) + "s")
    print("Obfuscated code written to: " + os.path.abspath(config["output"]))
    with open(config["output"], "w+",encoding="utf-8") as f:
        for line in obfuscated:
            f.write(line)
        f.close()