"""
description: Function and class annotation specifications in the project
functions: test
"""
# py文件中，如果全部为函数，顶部信息格式如上,description填写描述信息，functions填写函数名称
# Args:
# 列出每个参数的名字, 并在名字后使用一个冒号和一个空格,
# 分隔对该参数的描述.如果描述太长超过了单行80字符,使用2或者4个空格的悬挂缩进(与文件其他部分保持一致).
# 描述应该包括所需的类型和含义.
# Returns:
# 描述返回值的类型和语义. 如果函数返回None, 这一部分可以省略.
# Raises:
# 可能产生的异常


def test(name, age):
    """
    Description: Function description information
    Args:
        name: name information
        age: age information
    Returns:
        Returned information
    Raises:
         IOError: An error occurred accessing the bigtable.Table object.
    """
    name = 'tom'
    age = 11
    return name, age


# description: Function and class annotation specifications in the project
# class: SampleClass
# py文件中，如果全部为类，顶部信息格式如上,description填写描述信息，class填写类名称,用 三引号，不用#
# 类应该在其定义下有一个用于描述该类的文档字符串.
# 如果你的类有公共属性(Attributes),
# 那么文档中应该有一个属性(Attributes)段.
# 并且应该遵守和函数参数相同的格式.


class SampleClass():
    """
    Summary of class here.
    Longer class information....
    Attributes:
        likes_spam: A boolean indicating if we like SPAM or not.
        eggs: An integer count of the eggs we have laid.
    """

    def __init__(self, likes_spam=False):
        """Inits SampleClass with blah."""
        self.likes_spam = likes_spam
        self.eggs = "eggs"

    def public_method_one(self, egg, fun):
        """
        Description: Function description information
        Args:
            egg: egg information
            fun: fun information
        Returns:
            Returned information
        Raises:
            AttributeError
        """
        self.eggs = "eggs"
        egg = "egg"
        fun = "fun"
        return egg, fun

    def public_method_two(self, tom):
        """
         Description: Function description information
        Args:
            tom: tom information
        Returns:
            Returned information
        Raises:
            Error
        """
        self.likes_spam = True
        tom = 'cat'
        return tom
