import functools
try:from timer_tool import timer # pip install timer-tool
except ImportError:timer=lambda func:func

ENABLE_CACHE = False
INDENT = 4
def using_namespace(obj,scope,except_=[],internal=False):
    for name in dir(obj):
        if not internal and name.startswith("_"):continue
        if name in except_:continue
        scope[name]=getattr(obj,name)

def unuse_namespace(obj,scope,except_=[],internal=False):
    # 参数应和之前调用using_namespace的一致
    for name in dir(obj):
        if not internal and name.startswith("_"):continue
        if name in except_:continue
        del scope[name]

def define_enum(names,local,start=0):
    # names: 字符串列表，或者以","和\n分割的字符串
    if isinstance(names,str):
        ignored=str.maketrans("","","\n ")
        names=names.translate(ignored).split(",")
    for i,name in enumerate(names,start):
        local[name]=i

class Symbol:
    define_enum(
"""ADD, SUB, MUL, DIV, MOD, POW, FLOOR_DIV,
AND, OR, XOR, NOT,
LT, LE, EQ, NE, GT, GE,
LSHIFT, RSHIFT,
BIT_AND, BIT_OR, BIT_XOR, BIT_NOT,
ASSIGN,NEG,POS,
PLUS_ASSIGN, MINUS_ASSIGN, MUL_ASSIGN, DIV_ASSIGN, MOD_ASSIGN, POW_ASSIGN, FLOOR_DIV_ASSIGN,
LSHIFT_ASSIGN, RSHIFT_ASSIGN, AND_ASSIGN, OR_ASSIGN, XOR_ASSIGN, HIGHEST""",
        locals()
    )

    priority = [
        # 优先级最低：赋值运算符
        (ASSIGN, PLUS_ASSIGN, MINUS_ASSIGN, MUL_ASSIGN, DIV_ASSIGN, MOD_ASSIGN, POW_ASSIGN,
         FLOOR_DIV_ASSIGN, LSHIFT_ASSIGN, RSHIFT_ASSIGN, AND_ASSIGN, OR_ASSIGN, XOR_ASSIGN),
        # 逻辑运算符
        (OR, AND),
        # 比较运算符
        (LT, LE, EQ, NE, GT, GE),
        # 位运算符
        (BIT_OR,),
        (BIT_XOR,),
        (BIT_AND,),
        # 位移运算符
        (LSHIFT, RSHIFT),
        # 算术运算符
        (ADD, SUB),
        (MUL, DIV, MOD, FLOOR_DIV),
        # 幂运算符
        (POW,),
        # 一元运算符
        (NOT, BIT_NOT, NEG, POS),
        # 最高优先级的占位符
        (HIGHEST,),
    ]

PRIORITY={}
for level in range(len(Symbol.priority)):
    for symbol in Symbol.priority[level]:
        PRIORITY[symbol]=level

using_namespace(Symbol,globals(),["priority"])

def ck(obj,symbol):
    # 如对于x + (y * z)，outer_priority为"+"，inner_priority为"*"
    outer_priority=PRIORITY[symbol]
    inner_priority=PRIORITY[getattr(obj,"_DynObj__last_symbol",HIGHEST)]
    fmt="({!r})" if outer_priority > inner_priority else "{!r}"
    return fmt.format(obj)


def magic_meth(meth):
    @functools.wraps(meth)
    def override(self,*args,**kw):
        return getattr(self,meth.__name__)(*args,**kw)
    return override

# 用于表达式求值
class DynObj:
    _cache = {}
    if ENABLE_CACHE:
        def __new__(cls, code, symbol=HIGHEST):
            if code in cls._cache:
                return cls._cache[code]
            instance = super().__new__(cls)
            cls._cache[code] = instance
            return instance

    def __init__(self,code,symbol=HIGHEST):
        self.__code=code # __code仅在__str__和__repr__使用
        self.__last_symbol=symbol
    def __call__(self,*args,**kw):
        new_code="{}({}{})".format(
            self, ", ".join(repr(elem) for elem in args),
            ", "+", ".join("{}={!r}".format(k,v) for k,v in kw.items()) \
                if kw else "")
        return DynObj(new_code)
    def __getattr__(self,name):
        new_code="{}.{}".format(self,name)
        return DynObj(new_code)
    def __str__(self):
        return self.__code
    def __repr__(self):
        return self.__code

    # 算术运算符
    def __add__(self, other): return DynObj(f"{ck(self,ADD)} + {ck(other,ADD)}",ADD)
    def __sub__(self, other): return DynObj(f"{ck(self,SUB)} - {ck(other,SUB)}",SUB)
    def __mul__(self, other): return DynObj(f"{ck(self,MUL)} * {ck(other,MUL)}",MUL)
    def __truediv__(self, other):
        return DynObj(f"{ck(self, DIV)} / {ck(other, DIV)}", DIV)
    def __floordiv__(self, other):
        return DynObj(f"{ck(self, FLOOR_DIV)} // {ck(other, FLOOR_DIV)}", FLOOR_DIV)
    def __mod__(self, other): return DynObj(f"{ck(self, MOD)} % {ck(other, MOD)}", MOD)
    def __pow__(self, other): return DynObj(f"{ck(self, POW)} ** {ck(other, POW)}", POW)
    def __lshift__(self, other):
        return DynObj(f"{ck(self, LSHIFT)} << {ck(other, LSHIFT)}", LSHIFT)
    def __rshift__(self, other):
        return DynObj(f"{ck(self, RSHIFT)} >> {ck(other, RSHIFT)}", RSHIFT)
    def __and__(self, other): return DynObj(f"{ck(self, BIT_AND)} & {ck(other, BIT_AND)}", BIT_AND)
    def __xor__(self, other): return DynObj(f"{ck(self, BIT_XOR)} ^ {ck(other, BIT_XOR)}", BIT_XOR)
    def __or__(self, other): return DynObj(f"{ck(self, BIT_OR)} | {ck(other, BIT_OR)}", BIT_OR)

    # 反向算术运算符
    def __radd__(self, other): return DynObj(f"{ck(other, ADD)} + {ck(self, ADD)}", ADD)
    def __rsub__(self, other): return DynObj(f"{ck(other, SUB)} - {ck(self, SUB)}", SUB)
    def __rmul__(self, other): return DynObj(f"{ck(other, MUL)} * {ck(self, MUL)}", MUL)
    def __rtruediv__(self, other):
        return DynObj(f"{ck(other, DIV)} / {ck(self, DIV)}", DIV)
    def __rfloordiv__(self, other):
        return DynObj(f"{ck(other, FLOOR_DIV)} // {ck(self, FLOOR_DIV)}", FLOOR_DIV)
    def __rmod__(self, other): return DynObj(f"{ck(other, MOD)} % {ck(self, MOD)}", MOD)
    def __rpow__(self, other): return DynObj(f"{ck(other, POW)} ** {ck(self, POW)}", POW)
    def __rlshift__(self, other):
        return DynObj(f"{ck(other, LSHIFT)} << {ck(self, LSHIFT)}", LSHIFT)
    def __rrshift__(self, other):
        return DynObj(f"{ck(other, RSHIFT)} >> {ck(self, RSHIFT)}", RSHIFT)
    def __rand__(self, other): return DynObj(f"{ck(other, BIT_AND)} & {ck(self, BIT_AND)}", BIT_AND)
    def __rxor__(self, other): return DynObj(f"{ck(other, BIT_XOR)} ^ {ck(self, BIT_XOR)}", BIT_XOR)
    def __ror__(self, other): return DynObj(f"{ck(other, BIT_OR)} | {ck(self, BIT_OR)}", BIT_OR)

    # 增量赋值运算符
    @magic_meth
    def __iadd__(self, other): pass
    @magic_meth
    def __isub__(self, other): pass
    @magic_meth
    def __imul__(self, other): pass
    @magic_meth
    def __itruediv__(self, other): pass
    @magic_meth
    def __ifloordiv__(self, other): pass
    @magic_meth
    def __imod__(self, other): pass
    @magic_meth
    def __ipow__(self, other): pass

    # 比较运算符
    def __lt__(self, other): return DynObj(f"{ck(self, LT)} < {ck(other, LT)}", LT)
    def __le__(self, other): return DynObj(f"{ck(self, LE)} <= {ck(other, LE)}", LE)
    def __eq__(self, other): return DynObj(f"{ck(self, EQ)} == {ck(other, EQ)}", EQ)
    def __ne__(self, other): return DynObj(f"{ck(self, NE)} != {ck(other, NE)}", NE)
    def __gt__(self, other): return DynObj(f"{ck(self, GT)} > {ck(other, GT)}", GT)
    def __ge__(self, other): return DynObj(f"{ck(self, GE)} >= {ck(other, GE)}", GE)

    # 一元运算符
    def __neg__(self): return DynObj(f"-{ck(self, NEG)}", NEG)
    def __pos__(self): return DynObj(f"+{ck(self, POS)}", POS)
    def __abs__(self): return DynObj(f"abs({self})")
    def __invert__(self): return DynObj(f"~{ck(self, BIT_NOT)}", BIT_NOT)

    # 容器协议
    def __len__(self): return DynObj(f"len({self})")
    def __getitem__(self, key): return DynObj(f"{self}[{key!r}]")
    #def __setitem__(self, key, value): return DynObj(f"{self}[{key!r}] = {value!r}")
    #def __delitem__(self, key): return DynObj(f"del {self}[{key!r}]")
    #def __contains__(self, item):pass

    # 类型转换 (待实现)
    #def __int__(self):pass
    #def __float__(self):pass
    #def __complex__(self):pass
    #def __round__(self, ndigits=None):pass

    # 上下文管理
    @magic_meth
    def __enter__(self): pass
    @magic_meth
    def __exit__(self, exc_type, exc_value, traceback): pass

# -- 链式调用部分 --
_var_num = 0
def new_var():
    global _var_num
    name=f"var{_var_num}"
    _var_num += 1
    return name

def magic_meth_chained(fmt = None, use_newvar = True, indent_delta = 0, export = False):
    # use_newvar: 是否会生成新的返回值变量，为False时用于+=, -=等运算符
    # indent_delta: 缩进的变化量。export: 是否导出为其他类型
    if not use_newvar and export:
        raise ValueError("can't disable use_newvar while export is set to True")

    def magic_meth_chained_inner(meth):
        @functools.wraps(meth)
        def override(self,*args,**kw):
            chain = self._ChainedDynObj__chain
            kw["_self"] = self._ChainedDynObj__name
            if use_newvar:
                var_name=new_var()
                kw["_var"] = var_name
            if fmt is not None:
                new_code = fmt.format(*args, **kw)
                chain.add_code(new_code) # 加入新的一行代码

            chain.indent += indent_delta # 变化缩进

            if export:
                return chain.eval_value(var_name)
            if use_newvar:
                return ChainedDynObj(chain,var_name)
            return self

        return override
    return magic_meth_chained_inner

class ObjChain:
    def __init__(self, codes = None, objects = None):
        self.codes = codes if codes is not None else []
        self.objects = objects if objects is not None else []
        self.indent = 0
        self.exec_lineno = 0 # 导出中上次执行到的行号（确保代码只执行一次）
        self.scope = {} # 上次执行的命名空间
        self.export_funcs = {} # 哪些函数需要导出（键为对象的变量名，由于变量名是唯一的）
        self.export_attrs = {} # 哪些属性需要导出（键为对象的变量名）
    def repr(self,obj):
        for item in self.objects:
            if obj is item:
                return obj._ChainedDynObj__name
        return repr(obj)
    def add_code(self,code_line):
        self.codes.append(" "*(self.indent*INDENT)+code_line)

    def new_object(self,code_line,name,export_funcs=None,export_attrs=None):
        self.add_code(code_line)
        if export_funcs is None:export_funcs = []
        if export_attrs is None:export_attrs = []
        self.export_funcs[name] = export_funcs # 添加到对象的要导出的函数
        self.export_attrs[name] = export_attrs
        return ChainedDynObj(self,name)
    def get_code(self, start_lineno=None, end_lineno=None):
        # 获取代码段
        if start_lineno is None:start_lineno = 0
        if end_lineno is None:end_lineno = len(self.codes)
        return "\n".join(self.codes[start_lineno:end_lineno])
    def eval_value(self,var_name):
        exec(self.get_code(self.exec_lineno),self.scope) # 从self.exec_lineno继续执行后面的代码
        self.exec_lineno = len(self.codes)
        return self.scope[var_name]

class ChainedDynObj:
    def __init__(self,chain,name,export_call=False):
        self.__chain=chain
        chain.objects.append(self)
        self.__name=name
        self.__export_call=export_call
    def __call__(self,*args,**kw):
        var_name=new_var()
        new_code="{} = {}({}{})".format(
            var_name, self.__name, ", ".join(
                self.__chain.repr(elem) for elem in args),
            ", "+", ".join("{}={}".format(
                k,self.__chain.repr(v)) for k,v in kw.items()) \
            if kw else "")
        self.__chain.add_code(new_code)

        if self.__export_call:
            return self.__chain.eval_value(var_name)
        return ChainedDynObj(self.__chain,var_name)

    #@magic_meth_chained("{_var} = {_self}.{}")
    def __getattr__(self,attr):
        var_name=new_var()
        new_code = f"{var_name} = {self.__name}.{attr}"
        self.__chain.add_code(new_code)

        if attr in self.__chain.export_attrs[self.__name]:
            return self.__chain.eval_value(var_name)
        return ChainedDynObj(self.__chain,var_name,
                             attr in self.__chain.export_funcs[self.__name])
    @magic_meth_chained("{_var} = str({_self})",export=True)
    def __str__(self): pass
    @magic_meth_chained("{_var} = repr({_self})",export=True)
    def __repr__(self): pass

    # 算术运算符
    @magic_meth_chained("{_var} = {_self} + {!r}")
    def __add__(self, other): pass
    @magic_meth_chained("{_var} = {_self} - {!r}")
    def __sub__(self, other): pass
    @magic_meth_chained("{_var} = {_self} * {!r}")
    def __mul__(self, other): pass
    @magic_meth_chained("{_var} = {_self} / {!r}")
    def __truediv__(self, other): pass
    @magic_meth_chained("{_var} = {_self} // {!r}")
    def __floordiv__(self, other): pass
    @magic_meth_chained("{_var} = {_self} % {!r}")
    def __mod__(self, other): pass
    @magic_meth_chained("{_var} = {_self} ** {!r}")
    def __pow__(self, other): pass
    @magic_meth_chained("{_var} = {_self} << {!r}")
    def __lshift__(self, other): pass
    @magic_meth_chained("{_var} = {_self} >> {!r}")
    def __rshift__(self, other): pass
    @magic_meth_chained("{_var} = {_self} & {!r}")
    def __and__(self, other): pass
    @magic_meth_chained("{_var} = {_self} ^ {!r}")
    def __xor__(self, other): pass
    @magic_meth_chained("{_var} = {_self} | {!r}")
    def __or__(self, other): pass

    # 反向算术运算符
    @magic_meth_chained("{_var} = {!r} - {_self}")
    def __radd__(self, other): pass
    @magic_meth_chained("{_var} = {!r} - {_self}")
    def __rsub__(self, other): pass
    @magic_meth_chained("{_var} = {!r} * {_self}")
    def __rmul__(self, other): pass
    @magic_meth_chained("{_var} = {!r} / {_self}")
    def __rtruediv__(self, other): pass
    @magic_meth_chained("{_var} = {!r} // {_self}")
    def __rfloordiv__(self, other): pass
    @magic_meth_chained("{_var} = {!r} % {_self}")
    def __rmod__(self, other): pass
    @magic_meth_chained("{_var} = {!r} ** {_self}")
    def __rpow__(self, other): pass
    @magic_meth_chained("{_var} = {!r} << {_self}")
    def __rlshift__(self, other): pass
    @magic_meth_chained("{_var} = {!r} >> {_self}")
    def __rrshift__(self, other): pass
    @magic_meth_chained("{_var} = {!r} & {_self}")
    def __rand__(self, other): pass
    @magic_meth_chained("{_var} = {!r} ^ {_self}")
    def __rxor__(self, other): pass
    @magic_meth_chained("{_var} = {!r} | {_self}")
    def __ror__(self, other): pass

    # 增量赋值运算符
    @magic_meth_chained("{_self} += {!r}", False)
    def __iadd__(self, other): pass
    @magic_meth_chained("{_self} -= {!r}", False)
    def __isub__(self, other): pass
    @magic_meth_chained("{_self} *= {!r}", False)
    def __imul__(self, other): pass
    @magic_meth_chained("{_self} /= {!r}", False)
    def __itruediv__(self, other): pass
    @magic_meth_chained("{_self} //= {!r}", False)
    def __ifloordiv__(self, other): pass
    @magic_meth_chained("{_self} %= {!r}", False)
    def __imod__(self, other): pass
    @magic_meth_chained("{_self} **= {!r}", False)
    def __ipow__(self, other): pass

    # 比较运算符
    @magic_meth_chained("{_var} = {_self} < {!r}")
    def __lt__(self, other): pass
    @magic_meth_chained("{_var} = {_self} <= {!r}")
    def __le__(self, other): pass
    @magic_meth_chained("{_var} = {_self} == {!r}")
    def __eq__(self, other): pass
    @magic_meth_chained("{_var} = {_self} != {!r}")
    def __ne__(self, other): pass
    @magic_meth_chained("{_var} = {_self} > {!r}")
    def __gt__(self, other): pass
    @magic_meth_chained("{_var} = {_self} >= {!r}")
    def __ge__(self, other): pass

    # 一元运算符
    @magic_meth_chained("{_var} = -{_self}")
    def __neg__(self): pass
    @magic_meth_chained("{_var} = +{_self}")
    def __pos__(self): pass
    @magic_meth_chained("{_var} = abs({_self})")
    def __abs__(self): pass
    @magic_meth_chained("{_var} = ~{_self}")
    def __invert__(self): pass

    # 容器协议
    @magic_meth_chained("{_var} = len({_self})")
    def __len__(self): pass
    @magic_meth_chained("{_var} = {_self}[{!r}]")
    def __getitem__(self, key): pass
    @magic_meth_chained("{_self}[{!r}] = {!r}", False)
    def __setitem__(self, key, value): pass
    @magic_meth_chained("del {_self}[{!r}]", False)
    def __delitem__(self, key): pass
    @magic_meth_chained("{_var} = {!r} in {_self}")
    def __contains__(self, item):pass

    # 类型转换
    @magic_meth_chained("{_var} = int({_self})",export=True)
    def __int__(self):pass
    @magic_meth_chained("{_var} = float({_self})",export=True)
    def __float__(self):pass
    @magic_meth_chained("{_var} = complex({_self})",export=True)
    def __complex__(self):pass
    @magic_meth_chained("{_var} = round({_self}, {!r})",export=True)
    def __round__(self, ndigits=None):pass

    # 上下文管理
    @magic_meth_chained("with {_self}:",False,1)
    def __enter__(self): pass
    @magic_meth_chained("",False,-1)
    def __exit__(self, exc_type, exc_value, traceback): pass


def test():
    _1=DynObj("1");_2=DynObj("2")
    print(-(_1+_2)*_1)

@timer
def test_perf():
    def recursion(x=None,recurse=10):
        if recurse<=0:return x
        return recursion(-(x+x)*x/x//x,recurse-1)

    x=DynObj("x")
    obj=recursion(x,10)
    print(recursion(x,1),":",len(repr(obj)))

def test_proxy):
    chain = ObjChain()
    np = chain.new_object("import numpy as np","np")
    plt = chain.new_object("import matplotlib.pyplot as plt","plt",
                           export_funcs = ["show"])

    # 测试调用伪numpy, matplotlib模块
    arr = np.array([1, 2, 3, 4, 5])  
    arr_squared = arr ** 2
    mean = np.mean(arr)
    std_dev = np.std(arr)
    print(mean, std_dev)

    plt.plot(arr, arr_squared)
    plt.show()

    print(chain.get_code())
    #exec(chain.get_code())

if __name__=="__main__":test_proxy()