# 实现简单的不可变的链式求值对象（备用，也是后续ProxiedObj的原型）
import functools
try:from timer_tool import timer # pip install timer-tool
except ImportError:timer=lambda func:func
from pyobject.objproxy.utils import format_func_call

ENABLE_CACHE = False

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

def magic_meth(meth): # 用于无法获知具体表达式的魔法方法调用（备用函数）
    @functools.wraps(meth)
    def override(self,*args,**kw):
        return DynObj(f"{ck(self, HIGHEST)}.{meth.__name__}") # 优先级使用默认的HIGHEST
    return override

# 能包装表达式链式求值的对象（不可变）
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
        self.__last_symbol=symbol # pylint: disable=unused-private-member
    def __call__(self,*args,**kw):
        new_code="{}({})".format(self, format_func_call(args,kw))
        return DynObj(new_code)
    def __getattr__(self,name):
        new_code="{}.{}".format(self,name)
        return DynObj(new_code)
    def __str__(self):
        return self.__code
    def __repr__(self):
        return self.__code

    # 算术运算符
    def __add__(self, other): return DynObj(f"{ck(self, ADD)} + {ck(other,ADD)}",ADD)
    def __sub__(self, other): return DynObj(f"{ck(self, SUB)} - {ck(other,SUB)}",SUB)
    def __mul__(self, other): return DynObj(f"{ck(self, MUL)} * {ck(other,MUL)}",MUL)
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
    #def __len__(self): return DynObj(f"len({self})")
    def __getitem__(self, key): return DynObj(f"{self}[{key!r}]")
    #def __setitem__(self, key, value): return DynObj(f"{self}[{key!r}] = {value!r}")
    #def __delitem__(self, key): return DynObj(f"del {self}[{key!r}]")
    #def __contains__(self, item):pass

    # 类型转换 (待实现)
    #def __int__(self):pass
    #def __float__(self):pass
    #def __complex__(self):pass
    #def __round__(self, ndigits=None):pass

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

if __name__ == "__main__":test_perf()