<span class="badge-placeholder">[![Stars](https://img.shields.io/github/stars/qfcy/pyobject)](https://img.shields.io/github/stars/qfcy/pyobject)</span>
<span class="badge-placeholder">[![GitHub release](https://img.shields.io/github/v/release/qfcy/pyobject)](https://github.com/qfcy/pyobject/releases/latest)</span>
<span class="badge-placeholder">[![License: MIT](https://img.shields.io/github/license/qfcy/pyobject)](https://github.com/qfcy/pyobject/blob/main/LICENSE)</span>

pyobject - 一个多功能合一的提供操作Python对象底层工具的Python包, 支持几乎所有Python 3版本。
A multifunctional all-in-one utility tool for managing internal Python objects, compatible with nearly all Python 3 versions.

**The English introduction is shown below the Chinese version.**

## 子模块

pyobject.\_\_init\_\_ - 显示和输出Python对象的各个属性值

pyobject.browser - 调用tkinter，浏览Python对象的图形界面

pyobject.code - Python 底层字节码(bytecode)的操作工具

pyobject.search - 以一个对象为起点，查找和搜索能到达的所有python对象

pyobject.objproxy - 实现一个通用的对象代理，能够代理任意Python对象，包括模块，函数和类

pyobject.pyobj_extension - C扩展模块, 提供操作Python对象底层的函数

## 包含的函数

**describe(obj, level=0, maxlevel=1, tab=4, verbose=False, file=sys.stdout)**:

以`属性名: 值`格式，打印出对象的各个属性，便于实时调试对象。（别名为`desc()`）  

- maxlevel: 打印对象属性的层数。
- tab: 缩进的空格数，默认为4。
- verbose: 一个布尔值，是否打印出对象的特殊方法（如`__init__`）。
- file: 一个类似文件的对象，用于打印输出。

**browse(object, verbose=False, name='obj')**:

用图形界面浏览任意的Python对象，需要tkinter库。

- verbose: 与describe相同，是否打印出对象的特殊方法（如`__init__`）。

函数browse()的图形界面如下（中文的版本可在包目录内的[other/browser_chs_locale.py](https://github.com/qfcy/pyobject/blob/main/pyobject/other/browser_chs_locale.py)中找到）：

![browse函数界面图片](https://i-blog.csdnimg.cn/blog_migrate/3d67b32633815a54c8c9d0c370248318.png)

**bases(obj, level=0, tab=4)**:

bases(obj) - 打印出对象的基类，以及继承顺序。

- tab: 缩进的空格数，默认为4。

## 用于对象搜索的函数

**make_list(start_obj, recursions=2, all=False)**:

创建一个对象的列表，列表中无重复的对象。

- start: 开始搜索的对象
- recursion: 递归次数
- all: 是否将对象的特殊属性（如`__init__`）加入列表

**make_iter(start_obj, recursions=2, all=False)**:

功能、参数与make_list相同，但创建迭代器，且迭代器中可能有重复的对象。


**search(obj, start, recursions=3, search_str=False)**:

从一个起点开始搜索对象，如`search(os, sys, 3)`返回`["sys.modules['site'].os", "sys.modules['os']", ...]`的结果。

- obj: 待搜索的对象
- start: 起点对象
- recursion: 递归次数
- search_str: 是否是查找字符串子串

## 类: `pyobject.Code`

类Code提供了Python字节码(bytecode)对象的封装，便于操作Python字节码。

Python内部的字节码对象`CodeType`，如`func.__code__`，是不可变的，这里的Code类提供了一个**可变**的字节码对象，以及一系列方法，使得操作底层字节码变得更容易。

此外和Java字节码不同，Python字节码是**不跨版本**的，不同版本Python解释器的字节码互不兼容，

而Code类提供了字节码的**通用接口**，支持**3.4至3.14**之间的所有Python版本（甚至PyPy的.pyc格式），简化了复杂的版本兼容性问题。

#### 构造函数（`Code(code=None)`）
`code`参数可以是现有的 `CodeType` 对象，或者另一个 `Code` 实例。如果未提供`code，则会创建一个默认的 `CodeType` 对象。

#### 属性

- `_code`: 当前Code对象的内部字节码，如应使用`exec(c._code)`或`exec(c.to_code())`，而不是直接使用`exec(c)`。

以下是Python内置字节码的属性（也是`Code`对象的属性）。Python内部的字节码`CodeType`是不可变的，这些属性只读，但`Code`对象可变，也就是这些属性都**可修改**:

- `co_argcount`: 位置参数的数量（包括有默认值的参数）。
- `co_cellvars`: 一个包含被嵌套函数所引用的局部变量名称的元组。
- `co_code`: 一个表示字节码指令序列的`bytes`类型，存放真正的二进制字节码。
- `co_consts`: 一个包含字节码所使用的字面值的元组。
- `co_filename`: 被编码代码所在的文件名。
- `co_firstlineno`: 字节码对应到源文件首行的行号，在解释器内部和`co_lnotab`结合使用，用来在Traceback中输出精确的行号。
- `co_flags`: 一个以整数编码表示的多个解释器所用的旗标。
- `co_freevars`: 一个包含自由变量名称的元组。
- `co_kwonlyargcount`: 仅关键字参数的数量。
- `co_lnotab`: 一个以编码表示的从字节码偏移量到行号的映射的字符串（Python 3.10开始，被`co_linetable`替代）。
- `co_name`: 字节码对应的函数/类名称。
- `co_names`: 一个包含字节码所使用的名称的元组。
- `co_nlocals`: 函数使用的局部变量数量（包括参数）。
- `co_stacksize`: 执行字节码需要的栈大小。
- `co_varnames`: 一个包括局部变量名称的元组（以参数名打头）。

3.8及以上版本新增的属性:

- `co_posonlyargcount`:  仅位置参数的数量，在Python 3.8引入。
- `co_linetable`: 行号映射数据，从3.10开始作为`co_lnotab`属性的替代。
- `co_exceptiontable`: 异常表数据，Python 3.11引入。
- `co_qualname`: 字节码的全名，Python 3.11引入。

#### 方法

**主要方法**

- `exec(globals_=None, locals_=None)`：在全局和局部作用域字典中执行代码对象。
- `eval(globals_=None, locals_=None)`：在全局和局部作用域字典中执行代码对象，并获取返回值。
- `copy()`：复制一份`Code`对象，返回复制的副本。
- `to_code()`：将 `Code` 实例转换回内置的 `CodeType` 对象，和`c._code`相同。
- `to_func(globals_=None, name=None, argdefs=None, closure=None, kwdefaults=None)`：将代码对象转换为 Python 函数，参数用法和Python内置`FunctionTypes`实例化的参数相同。
- `get_flags()`：返回 `co_flags` 属性的标志名称列表，如`["NOFREE"]`。
- `get_sub_code(name)`：搜索代码的`co_consts`中的子代码，如函数、类定义等，不会递归搜索。返回搜索到的`Code`对象，未找到时抛出`ValueError`。

**序列化**

- `to_pycfile(filename)`：使用 `marshal` 模块将代码对象转储到 `.pyc` 文件中。
- `from_pycfile(filename)`：从 `.pyc` 文件创建 `Code` 实例。
- `from_file(filename)`：从 `.py` 或 `.pyc` 文件创建 `Code` 实例。
- `pickle(filename)`：将 `Code` 对象序列化为 pickle 文件。

**调试和检查**

- `show(*args, **kw)`：在内部调用`pyobject.desc`，显示代码对象的属性，参数用法和`desc()`的用法相同。
- `info()`：在内部调用`dis.show_code`，显示字节码的基本信息。
- `dis(*args, **kw)`：调用 `dis` 模块输出字节码的反汇编，和`dis.dis(c.to_code())`相同。
- `decompile(version=None, *args, **kw)`：调用 `uncompyle6` 库将代码对象反编译为源代码。（安装`pyobject`库时， `uncompyle6` 库是可选的。）

**工厂函数**

- `fromfunc(function)`：从 Python 函数对象创建 `Code` 实例，和`Code(func.__code__)`相同。
- `fromstring(string, mode='exec', filename='')`：从源代码字符串创建 `Code` 实例，参数用法和`compile`内置函数相同，在内部调用`compile()`。

#### 兼容性细节

- 属性`co_lnotab`：在3.10以上的版本中，如果尝试设置`co_lnotab`属性，会自动转换成设置`co_linetable`。


示例用法: (从doctest中摘取):

```python
>>> def f():print("Hello")
>>> c=Code.fromfunc(f) # 或 c=Code(f.__code__)
>>> c.co_consts
(None, 'Hello')
>>> c.co_consts=(None, 'Hello World!')
>>> c.exec()
Hello World!
>>>
>>> # 保存到 pickle 文件
>>> import os,pickle
>>> temp=os.getenv('temp')
>>> with open(os.path.join(temp,"temp.pkl"),'wb') as f:
...     pickle.dump(c,f)
...
>>> # 读取pickle文件，并重新执行读取到的字节码
>>> f=open(os.path.join(temp,"temp.pkl"),'rb')
>>> pickle.load(f).to_func()()
Hello World!
>>> # 转换为pyc文件，并导入pyc模块
>>> c.to_pycfile(os.path.join(temp,"temppyc.pyc"))
>>> sys.path.append(temp)
>>> import temppyc
Hello World!
>>> Code.from_pycfile(os.path.join(temp,"temppyc.pyc")).exec()
Hello World!
```

## 对象代理类`ObjChain`和`ProxiedObj`

`pyobject.objproxy`是一个强大的代理任何其他对象，生成调用对象的代码的工具，能够记录对象的详细访问和调用历史记录。
`ObjChain`是用于管理多个`ProxiedObj`对象的类封装，`ProxiedObj`是代理其他对象的类。  

示例用法：
```python
from pyobject import ObjChain

chain = ObjChain(export_attrs=["__array_struct__"])
np = chain.new_object("import numpy as np","np")
plt = chain.new_object("import matplotlib.pyplot as plt","plt",
                        export_funcs = ["show"])

# 测试调用代理后的numpy, matplotlib模块
arr = np.array(range(1,11))
arr_squared = arr ** 2
print(np.mean(arr)) # 输出平均值

plt.plot(arr, arr_squared) # 绘制y=x**2的图像
plt.show()

# 显示自动生成的调用numpy, matplotlib库的代码
print(f"Code:\n{chain.get_code()}\n")
print(f"Optimized:\n{chain.get_optimized_code()}")
```
输出效果：
```python
Code: # 未优化的代码，包含了对象的所有详细访问记录
import numpy as np
import matplotlib.pyplot as plt
var0 = np.array
var1 = var0(range(1, 11))
var2 = var1 ** 2
var3 = np.mean
var4 = var3(var1)
var5 = var1.mean
var6 = var5(axis=None, dtype=None, out=None)
ex_var7 = str(var4)
var8 = plt.plot
var9 = var8(var1, var2)
var10 = var1.to_numpy
var11 = var1.values
var12 = var1.shape
var13 = var1.ndim
...
var81 = var67.__array_struct__
ex_var82 = iter(var70)
ex_var83 = iter(var70)
var84 = var70.mask
var85 = var70.__array_struct__
var86 = plt.show
var87 = var86()

Optimized: # 优化后的代码
import numpy as np
import matplotlib.pyplot as plt
var1 = np.array(range(1, 11))
plt.plot(var1, var1 ** 2)
plt.show()
```

#### 详细用法

**`ObjChain`**  
- `ObjChain(export_funcs = None, export_attrs = None)`: 创建一个`ObjChain`对象，`export_funcs`为全局范围需要导出的函数列表，`export_attrs`为全局范围需要导出的属性列表。由于是全局范围，对所有变量有效。
- `new_object(code_line,name, export_funcs=None, export_attrs=None, use_target_obj=True)`: 新增一个对象，返回一个生成的`ProxiedObj`类型的代理对象，返回值可以直接当作普通对象使用。  
`code_line`是为了得到这个对象而需要执行的代码（如`"import numpy as np"`），`name`是执行之后对象放在的变量值（如`"np"`）。  
`export_funcs`和`export_attrs`是针对这个对象，需要导出的方法和属性列表。  
`use_target_obj`为是否实时创建一个代理的模板对象，并操作（详见“实现原理”一节）。  
- `add_existing_obj(obj, name)`: 添加现有的对象，返回一个`ProxiedObj`类型的代理对象。  
`obj`为对象，`name`为任意的变量名，用来在`ObjChain`生成的代码中，指代这个对象。  
- `get_code(start_lineno=None, end_lineno=None)`: 获取`ObjChain`生成的原始代码，`start_lineno`和`end_lineno`为从0开始的行号，如果未指定，则默认为开头和末尾。
- `get_optimized_code(no_optimize_vars=None, remove_internal=True, remove_export_type=True)`: 获取优化后的代码，内部使用了有向无环图(DAG)进行优化（详见“实现原理”一节）。  
`no_optimize_vars`: 不能移除的变量名的列表，如`["temp_var"]`。  
`remove_internal`: 是否移除执行代码本身时产生的内部代码。例如`plt.plot`和`arr`, `arr2`都是`ProxiedObj`对象，
如果`remove_internal`为`False`，调用`plt.plot(arr,arr2)`本身时生成的访问`arr`, `arr2`的内部代码，如`var13 = arr.ndim`不会被移除。  
`remove_export_type`: 是否移除无用的类型导出，如`str(var)`。  

**`ProxiedObj`**  

`ProxiedObj`为`ObjChain`的`new_object()`、`add_existing_obj()`返回的代理对象的类型，可以替代任何普通对象使用，但通常不建议直接使用`ProxiedObj`类本身的方法和属性。  

#### 实现原理

`ObjChain`类**追踪**所有加入`ObjChain`的对象，以及派生出的对象，并且维护一个包含被追踪的对象的命名空间字典，用于调用`exec`执行自身生成的代码。  
每个`ProxiedObj`对象属于一个`ObjChain`。`ProxiedObj`类的所有魔法方法（如`__call__`, `__getattr__`）都是被**重写**的，重写的方法一边将调用记录加入`ProxiedObj`属于的`ObjChain`，
一边调用自身代理的对象`__target_obj`（如果有）的相同魔法方法。  
当对`ProxiedObj`的操作返回了新的对象（如`obj.attr`返回新的属性）时，新的对象也会被`ObjChain`追踪，直到`ObjChain`内部形成一个从第一个对象开始，派生出的所有对象的**长链**。  
如果`ProxiedObj`存在`__target_obj`属性，则调用`ProxiedObj`的魔法方法时，会**同步**地调用`__target_obj`的魔法方法，并将返回的结果传递给下一个`ProxiedObj`的`__target_obj`属性。  
如果`__target_obj`属性不存在，`ProxiedObj`不会同步地调用魔法方法，而是生成一份调用记录的代码，**临时保存**在`ProxiedObj`中，直到出现了需要导出（`export`）的方法或属性，
才会一次性执行全部之前加入的代码，并返回结果。  

**代码优化的原理**

在代码中，变量的依赖关系可以表示为一个**图**，如语句`y = func(x)`可以表示为节点`x`有一条指向`y`的边。  
但由于`ProxiedObj`生成的代码中一个对象只能对应一个变量，变量不能被重新赋值（类似js的`const`），会形成一个有向无环图(DAG)。  
优化时首先找出只影响0个或1个其他变量（只指向0~1个其他节点）的变量，如果只影响一个变量，则将自身的值代入被影响的语句进行内联，否则直接去除自身。  
如：
```python
temp_var = [1,2,3]
unused_var = func(temp_var)
```
代码中`temp_var`只有一条指向`unused_var`的边，而`unused_var`没有任何指出的边。  
将`temp_var`的值代入`func(temp_var)`进行内联，得到`unused_var = func([1,2,3])`，再去掉`unused_var`，优化后的代码会变成`func([1,2,3])`。  

## 模块`pyobject.pyobj_extension`

本模块使用了C语言编写。可使用`import pyobject.pyobj_extension as pyobj_extension`, 导入该独立模块。其中包含的函数如下:

**convptr(pointer)**:

将整数指针转换为Python对象，与id()相反。

**py_decref(object, n)**:

将对象的引用计数减小1。

**py_incref(object, n)**:

将对象的引用计数增加1。

**getrealrefcount(obj)**:

获取调用本函数前对象的实际引用计数。和sys.getrefcount()不同，不考虑调用时新增的引用计数。(差值为`_REFCNT_DELTA`这个常量)  
如：getrealrefcount([])会返回0，因为退出getrealrefcount后列表[]不再被任何对象引用，而sys.getrefcount([])会返回1。  
另外，a=[];getrealrefcount(a)会返回1而不是2。

**setrefcount(obj, n)**:

设置对象的实际引用计数(调用函数前)为n，和getrealrefcount()相反，同样不考虑调用时新增的引用计数。

**getrefcount_nogil(obj)**和**setrefcount_nogil(obj,ref_data)**:

在Python 3.14+的无GIL版本中获取和设置引用计数，`ref_data`为`(ob_ref_local, ob_ref_shared)`，不考虑调用时新增的引用计数。(实验性)

*警告: 不恰当地调用这些函数可能导致Python崩溃。*

**list_in(obj, lst)**:

判断obj是否在列表或元组lst中。与Python内置的obj in lst调用多次==运算符(`__eq__`)相比，
本函数直接比较对象的指针，提高了效率。


**`pyobject`当前版本**: 1.3.0

## 更新日志:

2025-6-6(v1.3.0):性能优化，提升了pyobject.objproxy模块的性能。  
2025-4-30(v1.2.9):改进和增强了子模块pyobject.objproxy，重命名子模块pyobject.code_为pyobject.code。  
2025-3-31(v1.2.8):将pyobject.super_proxy重命名为pyobject.objproxy，并正式发布；修改了pyobject.pyobj_extension模块。  
2025-3-6(v1.2.7):为pyobject.browser新增了`dir()`中不存在的类属性（如`__flags__`, `__mro__`），修改了pyobj_extension模块。  
2025-2-15(v1.2.6):修复了pyobject.browser浏览过大对象的卡顿问题，改进了pyobject.code_模块，新增了正在开发中的反射库pyobject.super_proxy，
在pyobj_extension新增了`getrefcount_nogil`和`setrefcount_nogil`。  
2024-10-24(v1.2.5):修复了pyobject.browser在Windows下的高DPI支持，修改了pyobj_extension模块，以及其他改进。  
2024-8-12(v1.2.4):针对pyobject.code_增加了对3.10及以上版本的支持；进一步优化了search模块的搜索性能，以及一些其他修复和改进。  
2024-6-20(v1.2.3):更新了包内test目录下的.pyc文件加壳工具，并更新了pyobject.browser中的对象浏览器，添加了显示列表和字典项，后退、前进、刷新页面，以及新增、编辑和删除项等新特性。  
2022-7-25(v1.2.2):增加了操作Python底层对象引用, 以及对象指针的C语言模块pyobj_extension。  
2022-2-2(v1.2.0):修复了一些bug,优化了search模块的性能; code_中增加了Code类, browser中增加编辑属性功能, 增加了Code类的doctest。  


---

## Submodules:

pyobject.\_\_init\_\_ - Displays and outputs attribute values of Python objects.

pyobject.browser - Provides a visual interface to browse Python objects using tkinter.

pyobject.code - Provides tools for manipulating Python native bytecode.

pyobject.search - Implements the utility for locating the path to a specific object.

pyobject.objproxy - Implement a generic object proxy that can replace any Python object, including modules, functions, and classes

pyobject.pyobj_extension - A C extension module offering functions to manipulate low-level Python objects.

## Functions:

**describe(obj, level=0, maxlevel=1, tab=4, verbose=False, file=sys.stdout)**:

Printing all attributes of an object in `attribute: value` format for debugging purpose. The alias is `desc()`.  
- maxlevel: The depth of attribute levels to print.
- tab: Number of spaces for indentation, default is 4.
- verbose: Boolean indicating whether to print special methods (e.g., `__init__`).
- file: A file-like object for output.

**browse(object, verbose=False, name='obj')**:

Browse any Python objects in a graphical interface using tkinter.
- verbose: Same as in `describe`, whether to print special methods.

The graphical interface of the browse() function is shown below:

![browse function GUI](https://i-blog.csdnimg.cn/direct/79e4deceb28e457088479db44efe35f8.png)

**bases(obj, level=0, tab=4)**:

Prints base classes and the inheritance order of an object.
- tab: Number of spaces for indentation, default is 4.

## Functions for searching objects:

**make_list(start_obj, recursions=2, all=False)**:

Creates a list of objects without duplicates.
- start: The object to start searching from.
- recursion: Number of recursions.
- all: Whether to include special attributes (e.g., `__init__`) in the list.

**make_iter(start_obj, recursions=2, all=False)**:

Similar to make_list, but creates an iterator, which may contain duplicates.

**search(obj, start, recursions=3, search_str=False)**:

Searches for objects starting from a specified starting point. For example, `search(os, sys, 3)` returns results like `["sys.modules['site'].os", "sys.modules['os']", ...]`.
- obj: The object to search for.
- start: The starting object.
- recursion: Number of recursions.
- search_str: Whether to search substrings within strings.

## Class: `pyobject.Code`

The `Code` class provides a wrapper for Python bytecode objects, making it easier to manipulate Python bytecode.

Python's internal bytecode object, `CodeType` (e.g., `func.__code__`), is immutable. The `Code` class offers a **mutable** bytecode object and a set of methods to simplify operations on the underlying bytecode.

Unlike Java bytecode, Python bytecode is **not cross-version compatible**. Bytecode generated by different versions of the Python interpreter is incompatible.

The `Code` class provides a **universal interface** for bytecode, supporting all Python versions from **3.4 to 3.14** (including PyPy's `.pyc` format), simplifying complex version compatibility issues.

#### Constructor (`def __init__(self, code=None)`)

The `Code` class can be initialized with an existing `CodeType` object or another `Code` instance. If no argument is provided, a default `CodeType` object is created.

#### Attributes

- `_code`: The internal bytecode of the current `Code` object. Use `exec(c._code)` or `exec(c.to_code())` instead of directly using `exec(c)`.

The following are attributes of Python's built-in bytecode (also attributes of the `Code` object). While Python's internal `CodeType` bytecode is immutable and these attributes are read-only, the `Code` object is mutable, meaning these attributes can be **modified**:

- `co_argcount`: The number of positional arguments (including those with default values).
- `co_cellvars`: A tuple containing the names of local variables referenced by nested functions.
- `co_code`: A `bytes` object representing the sequence of bytecode instructions, storing the actual binary bytecode.
- `co_consts`: A tuple containing the literals used by the bytecode.
- `co_filename`: The filename of the source code being compiled.
- `co_firstlineno`: The first line number of the source code corresponding to the bytecode. Used internally by the interpreter in combination with `co_lnotab` to output precise line numbers in tracebacks.
- `co_flags`: An integer encoding multiple flags used by the interpreter.
- `co_freevars`: A tuple containing the names of free variables.
- `co_kwonlyargcount`: The number of keyword-only arguments.
- `co_lnotab`: A string encoding the mapping of bytecode offsets to line numbers (replaced by `co_linetable` in Python 3.10).
- `co_name`: The name of the function/class corresponding to the bytecode.
- `co_names`: A tuple containing the names used by the bytecode.
- `co_nlocals`: The number of local variables used by the function (including arguments).
- `co_stacksize`: The stack size required to execute the bytecode.
- `co_varnames`: A tuple containing the names of local variables (starting with argument names).

Attributes introduced in Python 3.8 and later:
- `co_posonlyargcount`: The number of positional-only arguments, introduced in Python 3.8.
- `co_linetable`: Line number mapping data, introduced in Python 3.10 as a replacement for `co_lnotab`.
- `co_exceptiontable`: Exception table data, introduced in Python 3.11.
- `co_qualname`: The qualified name of the bytecode, introduced in Python 3.11.

#### Methods

**Core Methods**

- `exec(globals_=None, locals_=None)`: Executes the code object within the provided global and local scope dictionaries.
- `eval(globals_=None, locals_=None)`: Executes the code object within the provided global and local scope dictionaries and returns the result.
- `copy()`: Creates a copy of the `Code` object and returns the duplicate.
- `to_code()`: Converts the `Code` instance back to a built-in `CodeType` object, equivalent to `c._code`.
- `to_func(globals_=None, name=None, argdefs=None, closure=None, kwdefaults=None)`: Converts the code object into a Python function. The parameters are the same as those used when instantiating Python's built-in `FunctionType`.
- `get_flags()`: Returns a list of flag names for the `co_flags` attribute, e.g., `["NOFREE"]`.
- `get_sub_code(name)`: Searches for sub-code objects (e.g., functions or class definitions) in the `co_consts` attribute. This method does not perform recursive searches. Returns the found `Code` object or raises a `ValueError` if not found.

**Serialization**

- `to_pycfile(filename)`: Dumps the code object into a `.pyc` file using the `marshal` module.
- `from_pycfile(filename)`: Creates a `Code` instance from a `.pyc` file.
- `from_file(filename)`: Creates a `Code` instance from a `.py` or `.pyc` file.
- `pickle(filename)`: Serializes the `Code` object into a pickle file.

**Debugging and Inspection**

- `show(*args, **kw)`: Internally calls `pyobject.desc` to display the attributes of the code object. The parameters are the same as those used in `desc()`.
- `info()`: Internally calls `dis.show_code` to display basic information about the bytecode.
- `dis(*args, **kw)`: Calls the `dis` module to output the disassembly of the bytecode, equivalent to `dis.dis(c.to_code())`.
- `decompile(version=None, *args, **kw)`: Calls the `uncompyle6` library to decompile the code object into source code. (The `uncompyle6` library is optional when installing the `pyobject` package.)

**Factory Functions**

- `fromfunc(function)`: Creates a `Code` instance from a Python function object, equivalent to `Code(func.__code__)`.
- `fromstring(string, mode='exec', filename='')`: Creates a `Code` instance from a source code string. The parameters are the same as those used in the built-in `compile` function, which is called internally.

#### Compatibility Details

- Attribute `co_lnotab`: In Python 3.10 and later, attempts to set the `co_lnotab` attribute will automatically be converted into setting the `co_linetable` attribute.

Example usage: (excerpted from the doctest):

```python
>>> def f():print("Hello")
>>> c=Code.fromfunc(f) # or c=Code(f.__code__)
>>> c.co_consts
(None, 'Hello')
>>> c.co_consts=(None, 'Hello World!')
>>> c.exec()
Hello World!
>>>
>>> # Save to pickle files
>>> import os,pickle
>>> temp=os.getenv('temp')
>>> with open(os.path.join(temp,"temp.pkl"),'wb') as f:
...     pickle.dump(c,f)
...
>>> # Execute bytecodes from pickle files
>>> f=open(os.path.join(temp,"temp.pkl"),'rb')
>>> pickle.load(f).to_func()()
Hello World!
>>> # Convert to pyc files and import them
>>> c.to_pycfile(os.path.join(temp,"temppyc.pyc"))
>>> sys.path.append(temp)
>>> import temppyc
Hello World!
>>> Code.from_pycfile(os.path.join(temp,"temppyc.pyc")).exec()
Hello World!
```

## Object Proxy Classes `ObjChain` and `ProxiedObj`

`pyobject.objproxy` is a powerful tool for proxying any other object and generating the code that calls the object. It is capable of recording detailed access and call history of the object.  
`ObjChain` is a class encapsulation used to manage multiple `ProxiedObj` objects, where `ProxiedObj` is a class that acts as a proxy to other objects.

Example usage:
```python
from pyobject import ObjChain

chain = ObjChain(export_attrs=["__array_struct__"])
np = chain.new_object("import numpy as np", "np")
plt = chain.new_object("import matplotlib.pyplot as plt", "plt",
                        export_funcs=["show"])

# Testing the pseudo numpy and matplotlib modules
arr = np.array(range(1, 11))
arr_squared = arr ** 2
print(np.mean(arr)) # Output the average value

plt.plot(arr, arr_squared) # Plot the graph of y=x**2
plt.show()

# Display the auto-generated code calling numpy and matplotlib libraries
print(f"Code:\n{chain.get_code()}\n")
print(f"Optimized:\n{chain.get_optimized_code()}")
```
Output:
```python
Code: # Unoptimized code that contains all detailed access records for objects
import numpy as np
import matplotlib.pyplot as plt
var0 = np.array
var1 = var0(range(1, 11))
var2 = var1 ** 2
var3 = np.mean
var4 = var3(var1)
var5 = var1.mean
var6 = var5(axis=None, dtype=None, out=None)
ex_var7 = str(var4)
var8 = plt.plot
var9 = var8(var1, var2)
var10 = var1.to_numpy
var11 = var1.values
var12 = var1.shape
var13 = var1.ndim
...
var81 = var67.__array_struct__
ex_var82 = iter(var70)
ex_var83 = iter(var70)
var84 = var70.mask
var85 = var70.__array_struct__
var86 = plt.show
var87 = var86()

Optimized: # Optimized code
import numpy as np
import matplotlib.pyplot as plt
var1 = np.array(range(1, 11))
plt.plot(var1, var1 ** 2)
plt.show()
```

#### Detailed Usage

**`ObjChain`**  
- `ObjChain(export_funcs=None, export_attrs=None)`: Creates an `ObjChain` object, where `export_funcs` is a list of functions to be exported at the global level, and `export_attrs` is a list of attributes to be exported at the global level. Since these are at global scope, they are effective for all variables.
- `new_object(code_line, name, export_funcs=None, export_attrs=None, use_target_obj=True)`: Adds a new object and returns a proxy object of type `ProxiedObj` that can be directly used as a normal object.  
`code_line` is the code that needs to be executed to obtain the object (e.g., `"import numpy as np"`), and `name` is the variable name in which the object is stored after execution (e.g., `"np"`).  
`export_funcs` and `export_attrs` are the lists of methods and attributes for this object that need to be exported.  
`use_target_obj` indicates whether to create a proxy template object in real-time and operate on it (see the "Implementation" section for details).
- `add_existing_obj(obj, name)`: Adds an existing object and returns a proxy object of type `ProxiedObj`.  
`obj` is the object to be added, and `name` is an arbitrary variable name that will be used to refer to this object in the code generated by `ObjChain`.
- `get_code(start_lineno=None, end_lineno=None)`: Retrieves the original code generated by `ObjChain`. `start_lineno` and `end_lineno` are line numbers starting from 0, and if not specified, they default to the beginning and end.
- `get_optimized_code(no_optimize_vars=None, remove_internal=True, remove_export_type=True)`: Retrieves the optimized code. Internally, a directed acyclic graph (DAG) is used for optimization (see the "Implementation" section).  
`no_optimize_vars`: A list of variable names that should not be removed, such as `["temp_var"]`.  
`remove_internal`: Whether to remove internal code generated during the execution of the code. For example, with `plt.plot` and `arr`, `arr2` being `ProxiedObj` objects, if `remove_internal` is `False`, the internal code generated by accessing `arr` and `arr2` during the call `plt.plot(arr, arr2)` (such as `var13 = arr.ndim`) will not be removed.  
`remove_export_type`: Whether to remove unnecessary type exports, such as `str(var)`.

**`ProxiedObj`**

`ProxiedObj` is the type of object returned by `ObjChain`'s `new_object()` and `add_existing_obj()` methods. It can be used as a substitute for any regular object, though it is generally not recommended to directly use the methods and properties of the `ProxiedObj` class itself.

#### Implementation Details

The `ObjChain` class **tracks** all objects added to an `ObjChain` as well as the objects derived from them, and it maintains a namespace dictionary containing the tracked objects to be used when calling `exec` to execute its own generated code.  
Each `ProxiedObj` object belongs to an `ObjChain`. All special magic methods (such as `__call__`, `__getattr__`) of the `ProxiedObj` class are **overridden**. The overridden methods both record the call history into the associated `ObjChain` and call the same magic method on the object's proxy target (`__target_obj`, if available).  
When operations on a `ProxiedObj` return a new object (such as when `obj.attr` returns a new attribute), the new object will also be tracked by the `ObjChain`, forming a **long chain** of all derived objects starting from the first object within the `ObjChain`.  
If the `ProxiedObj` has a `__target_obj` attribute, magic method calls on the `ProxiedObj` will synchronously call the corresponding magic method on the `__target_obj` and pass the result to the next `ProxiedObj` as its `__target_obj` property.  
If the `__target_obj` attribute does not exist, the `ProxiedObj` will not synchronously call the magic method. Instead, it will generate a record of the call code, temporarily storing it in the `ProxiedObj` until an export (`export`) method or attribute is needed, at which point all accumulated code is executed at once and the result is returned.

**Principle of Code Optimization**

In the code, the dependency relationship between variables can be represented as a **graph**. For instance, the statement `y = func(x)` can be represented as an edge from the node `x` to `y`.  
However, since in the code generated by `ProxiedObj` each object corresponds to a unique variable and the variables cannot be reassigned (similar to JavaScript's `const`), the result is a directed acyclic graph (DAG).  
During optimization, variables that affect 0 or 1 other variables (i.e., that point to 0-1 other nodes) are first identified. If a variable affects only one other variable, its value is inlined into the dependent statement; otherwise, the variable is simply removed.  
For example:
```python
temp_var = [1, 2, 3]
unused_var = func(temp_var)
```
Here, `temp_var` only has one edge pointing to `unused_var`, while `unused_var` does not point to any other node.  
By inlining the value of `temp_var` into `func(temp_var)`, the code becomes `unused_var = func([1,2,3])`. After removing `unused_var`, the optimized code is `func([1, 2, 3])`.

## Module: `pyobj_extension`

This module is written in C and can be imported directly using `import pyobject.pyobj_extension as pyobj_extension`. It includes the following functions:

**convptr(pointer)**:

Converts an integer pointer to a Python object, as a reverse of id().

**py_decref(obj)**:

Decreases the reference count of an object.

**py_incref(obj)**:

Increases the reference count of an object.

**getrealrefcount(obj)**:

Get the actual reference count of the object before calling this function.  
Unlike sys.getrefcount(), this function does not consider the additional reference count that is created when the function is called. (The difference is the constant `_REFCNT_DELTA`)  
For example, getrealrefcount([]) will return 0, because after exiting getrealrefcount, the list [] is no longer referenced by any object, whereas sys.getrefcount([]) will return 1.  
Additionally, a=[]; getrealrefcount(a) will return 1 instead of 2.

**setrefcount(obj, n)**:

Set the actual reference count of the object (before calling the function) to n.  
This is the opposite of getrealrefcount() and also does not consider the additional reference count created when the function is called.

**getrefcount_nogil(obj)** and **setrefcount_nogil(obj, ref_data)**:

In the GIL-free version of Python 3.14+, get and set reference counts, where `ref_data` is `(ob_ref_local, ob_ref_shared)`, without considering the reference counts added during the call. (Experimental)

*Warning: Improper use of these functions above may lead to crashes.*

**list_in(obj, lst)**:

Determine whether obj is in the sequence lst.
Compared to the built-in Python call "obj in lst" that invokes the "==" operator (`__eq__`) multiple times, this function directly compares the pointers to improve efficiency.


**Current Version of `pyobject`**: 1.3.0

## Change Log

2025-6-6(v1.3.0): Optimized the performance of the pyobject.objproxy module.  
2025-4-30(v1.2.9): Improved and enhanced the sub-module `pyobject.objproxy`, and renamed the sub-module `pyobject.code_` to `pyobject.code`.  
2025-3-31(v1.2.8): Renamed pyobject.super_proxy to pyobject.objproxy and officially released it; modified the pyobject.pyobj_extension module.  
2025-3-6 (v1.2.7): Added support for special class attributes excluded from `dir()` (such as `__flags__`, `__mro__`) in pyobject.browser and modified the pyobj_extension module.  
2025-2-15 (v1.2.6): Fixed the lag issue when browsing large objects in `pyobject.browser`, improved the `pyobject.code_` module, introduced a new reflection library `pyobject.super_proxy` currently in development, and added `getrefcount_nogil` and `setrefcount_nogil` to the `pyobj_extension` module.  
2024-10-24 (v1.2.5): Fixed high DPI support for `pyobject.browser` on Windows, modified the `pyobj_extension` module, along with other improvements.  
2024-08-12 (v1.2.4): Added support for Python versions 3.10 and above in `pyobject.code_`; further optimized search performance in the `search` module, along with various other fixes and improvements.  
2024-06-20 (v1.2.3): Updated the `.pyc` file packing tool in the `test` directory of the package, and enhanced the object browser in `pyobject.browser` with new features such as displaying lists and dictionary items, back, forward, refresh page options, as well as adding, editing, and deleting items.  
2022-07-25 (v1.2.2): Added a C language module `pyobj_extension` for manipulating Python's underlying object references and object pointers.  
2022-02-02 (v1.2.0): Fixed several bugs and optimized the performance of the `search` module; added the `Code` class in `code_`, introduced editing properties functionality in `browser`, and added doctests for the `Code` class.  
