pyobject - 一个提供操作Python对象底层工具的Python包, 包含一些子模块。A utility tool with some submodules for operating internal python objects.

**The English introduction is shown below the Chinese version.**

所包含模块:
=====================

pyobject.__init__ - 显示和输出Python对象的各个属性值

pyobject.browser - 以图形界面浏览Python对象

pyobject.code\_ - Python 字节码(bytecode)的操作工具

pyobject.search - 以一个起始对象为起点，查找和搜索能到达的所有python对象

pyobject.newtypes - 定义一些新的类型 (实验性)

pyobj_extension - C扩展模块, 提供操作Python对象底层的函数

包含的函数:
=====================

describe(obj, level=0, maxlevel=1, tab=4, verbose=False, file=sys.stdout)::

    "描述"一个对象,即打印出对象的各个属性。
    参数说明:
    maxlevel:打印对象属性的层数。
    tab:缩进的空格数,默认为4。
    verbose:一个布尔值,是否打印出对象的特殊方法(如__init__)。
    file:一个类似文件的对象，用于打印输出。

browse(object, verbose=False, name='obj')::

    以图形方式浏览一个Python对象。
    verbose:与describe相同,是否打印出对象的特殊方法(如__init__)

函数browse()的图形界面如下所示 (中文界面的版本可在模块目录内的test/browser_chs_locale.py中找到)：

.. image:: https://img-blog.csdnimg.cn/direct/3226cebc991a467f9844a1bafda9209d.png
    :alt: browse函数界面图片

objectname(obj)::

    objectname(obj) - 返回一个对象的名称,形如xxmodule.xxclass。
    如:objectname(int) -> 'builtins.int'

bases(obj, level=0, tab=4)::

    bases(obj) - 打印出该对象的基类
    tab:缩进的空格数,默认为4。

用于对象搜索的函数:
==========================

make_list(start_obj, recursions=2, all=False)::

    创建一个对象的列表, 列表中无重复的对象。
    start:开始搜索的对象
    recursion:递归次数
    all:是否将对象的特殊属性(如__init__)加入列表

make_iter(start_obj, recursions=2, all=False)::

    功能、参数与make_list相同, 但创建迭代器, 且迭代器中可能有重复的对象。

search(obj, start, recursions=3)::

    从一个起点开始搜索对象
    obj:待搜索的对象
    start:起点对象
    recursion:递归次数

类: ``pyobject.Code``
========================

类Code用于包装Python字节码对象(bytecode)，提供一个便利操作Python字节码的接口。

Python底层的bytecode对象，如func.__code__，是不可变的，鉴于此，Code类提供了一个可变的字节码对象，以及一系列操作字节码的函数，使得操作底层字节码对象变得更容易。

示例用法\: (从模块的doctest中摘取)::

    >>> def f():print("Hello")
    >>> c=Code.fromfunc(f) # 或 c=Code(f.__code__)
    >>> c.co_consts
    (None, 'Hello')
    >>> c.co_consts=(None, 'Hello World!')
    >>> c.exec()
    Hello World!
    >>>
    >>> import os,pickle
    >>> temp=os.getenv('temp')
    >>> with open(os.path.join(temp,"temp.pkl"),'wb') as f:
    ...     pickle.dump(c,f)
    ...
    >>> f=open(os.path.join(temp,"temp.pkl"),'rb')
    >>> pickle.load(f).to_func()()
    Hello World!
    >>>
    >>> c.to_pycfile(os.path.join(temp,"temppyc.pyc"))
    >>> sys.path.append(temp)
    >>> import temppyc
    Hello World!
    >>> Code.from_pycfile(os.path.join(temp,"temppyc.pyc")).exec()
    Hello World!


模块: ``pyobj_extension``
=============================

本模块使用了C语言编写。可直接使用import pyobj_extension, 导入该独立模块。其中包含的函数如下:

convptr(pointer)::

    将整数指针转换为Python对象，与id()相反。

py_decref(object, n)::

	将对象的引用计数减小1。

py_incref(object, n)::

    将对象的引用计数增加1。

getrealrefcount(obj)::

    获取调用本函数前对象的实际引用计数。和sys.getrefcount()不同，不考虑调用时新增的引用计数。
    如：getrealrefcount([])会返回0，因为退出getrealrefcount后列表[]不再被任何对象引用，而sys.getrefcount([])会返回1。
    另外，a=[];getrealrefcount(a)会返回1而不是2。

setrefcount(obj, n)::

    设置对象的实际引用计数(调用函数前)为n，和getrealrefcount()相反，同样不考虑调用时新增的引用计数。

*警告: 不恰当地调用这些函数可能导致Python崩溃。*

list_in(obj, lst)::

    判断obj是否在列表或元组lst中。与Python内置的obj in lst调用多次==运算符(__eq__)相比，
    本函数直接比较对象的指针，提高了效率。


Submodules:
===========

pyobject.__init__ - Displays and outputs attribute values of Python objects.

pyobject.browser - Provides a visual interface to browse Python objects.

pyobject.code\_ - Provides tools for manipulating Python native bytecode.

pyobject.search - Implements the utility for locating the path to a specific object.

pyobject.newtypes - Defines a few new types. (Experimental)

pyobj_extension - A C extension module offering functions to manipulate low-level Python objects.

Functions:
==========

describe(obj, level=0, maxlevel=1, tab=4, verbose=False, file=sys.stdout)::

    "Describes" an object by printing its attributes.
    Parameters:
    - maxlevel: The depth of attribute levels to print.
    - tab: Number of spaces for indentation, default is 4.
    - verbose: Boolean indicating whether to print special methods (e.g., __init__).
    - file: A file-like object for output.

browse(object, verbose=False, name='obj')::

    Graphically browse a Python object.
    - verbose: Same as in describe, whether to print special methods.

The graphical interface of the browse() function is shown below:

.. image:: https://i-blog.csdnimg.cn/direct/2dc8cc8912354e75ad142696ec42a666.png
    :alt: browse function interface image

objectname(obj)::

    Returns the name of an object in the format xxmodule.xxclass.
    Example: objectname(int) -> 'builtins.int'.

bases(obj, level=0, tab=4)::

    Prints the base classes of the object.
    - tab: Number of spaces for indentation, default is 4.

Functions for searching objects:
================================

make_list(start_obj, recursions=2, all=False)::

    Creates a list of objects without duplicates.
    - start: The object to start searching from.
    - recursion: Number of recursions.
    - all: Whether to include special attributes (e.g., __init__) in the list.

make_iter(start_obj, recursions=2, all=False)::

    Similar to make_list, but creates an iterator, which may contain duplicates.

search(obj, start, recursions=3)::

    Searches for objects starting from a specified point.
    - obj: The object to search for.
    - start: The starting object.
    - recursion: Number of recursions.

Class: ``pyobject.Code``
========================

The Code class wraps Python bytecode objects, providing a convenient interface for manipulation.

Python's underlying bytecode objects, such as func.__code__, are immutable. The Code class offers a mutable bytecode object and a suite of functions to manipulate bytecode, simplifying operations on these objects.

Example usage: (excerpted from the module's doctest)::

    >>> def f():print("Hello")
    >>> c=Code.fromfunc(f) # or c=Code(f.__code__)
    >>> c.co_consts
    (None, 'Hello')
    >>> c.co_consts=(None, 'Hello World!')
    >>> c.exec()
    Hello World!
    >>>
    >>> import os,pickle
    >>> temp=os.getenv('temp')
    >>> with open(os.path.join(temp,"temp.pkl"),'wb') as f:
    ...     pickle.dump(c,f)
    ...
    >>> f=open(os.path.join(temp,"temp.pkl"),'rb')
    >>> pickle.load(f).to_func()()
    Hello World!
    >>>
    >>> c.to_pycfile(os.path.join(temp,"temppyc.pyc"))
    >>> sys.path.append(temp)
    >>> import temppyc
    Hello World!
    >>> Code.from_pycfile(os.path.join(temp,"temppyc.pyc")).exec()
    Hello World!

Module: ``pyobj_extension``
===========================

This module is written in C and can be imported directly using import pyobj_extension. It includes the following functions:

convptr(pointer)::

    Converts an integer pointer to a Python object, as a reverse of id().

py_decref(obj)::

    Decreases the reference count of an object.

py_incref(obj)::

    Increases the reference count of an object.

getrealrefcount(obj)::

    Get the actual reference count of the object before calling this function.
    Unlike sys.getrefcount(), this function does not consider the additional reference count   that is created when the function is called.
    For example, getrealrefcount([]) will return 0, because after exiting getrealrefcount, the list [] is no longer referenced by any object, whereas sys.getrefcount([]) will return 1.
    Additionally, a=[]; getrealrefcount(a) will return 1 instead of 2.

setrefcount(obj, n)::

    Set the actual reference count of the object (before calling the function) to n.
    This is the opposite of getrealrefcount() and also does not consider the additional reference count created when the function is called.

*Warning: Improper use of these functions above may lead to crashes.*

list_in(obj, lst)::

    Determine whether obj is in the sequence lst.
	Compared to the built-in Python call "obj in lst" that invokes the "==" operator (__eq__) multiple times, this function directly compares the pointers to improve efficiency.


版本 Version:1.2.5

更新日志:

2024-10-24(v1.2.5):修复了pyobject.browser在Windows下的高DPI支持，修改了pyobj_extension模块，以及其他改进。

2024-8-12(v1.2.4):针对pyobject.code_增加了对3.10及以上版本的支持；进一步优化了search模块的搜索性能，以及一些其他修复和改进。

2024-6-20(v1.2.3):更新了包内test目录下的.pyc文件加壳工具，并更新了pyobject.browser中的对象浏览器，添加了显示列表和字典项，后退、前进、刷新页面，以及新增、编辑和删除项等新特性。

2022-7-25(v1.2.2):增加了操作Python底层对象引用, 以及对象指针的C语言模块pyobj_extension。

2022-2-2(v1.2.0):修复了一些bug,优化了search模块的性能; code_中增加了Code类, browser中增加编辑属性功能, 增加了Code类的doctest。

源码:见 https://github.com/qfcy/pyobject

作者 Author: 七分诚意 qq:3076711200

作者CSDN主页: https://blog.csdn.net/qfcy\_/