import pyobject,os
from setuptools import setup,Extension

try:os.chdir(os.path.split(__file__)[0])
except:pass

try:
    long_desc=open("README.rst",encoding="utf-8").read()
except OSError:
    long_desc=pyobject.__doc__

setup(
    name='pyobject',
    version=pyobject.__version__,
    description=pyobject.__doc__.replace('\n',''),
    long_description=long_desc,
    author=pyobject.__author__,
    author_email=pyobject.__email__,
    url="https://github.com/qfcy/pyobject",
    packages=['pyobject'],
    include_package_data=True,
    ext_modules=[Extension(
        "pyobj_extension",["pyobject/pyobj_extension.c"]
    )],
    keywords=["pyobject","python","object","utility","object browser",
        "bytecode","对象","字节码","面向对象编程","对象浏览器"
    ],
    classifiers=[
        'Programming Language :: Python',
        "Natural Language :: Chinese (Simplified)",
        "Topic :: Utilities",
        "Topic :: Software Development :: Bug Tracking",
        "Topic :: Software Development :: Debuggers",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
)
