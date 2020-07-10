"""
description: Function and class annotation specifications in the project
functions: test
"""
# In the PY file, if all are functions, the format of the top information is as above,
# the description information is filled in, and the function name is filled in functions
# Args:
# List the name of each parameter with a colon and a space after the name,
# Separate the description of this parameter.
# If the description is too long than 80 characters in a single line,
# use a hanging indent of 2 or 4 spaces (consistent with the rest of the file)
# The description should include the type and meaning required
# Returns:
# Describes the type and semantics of the return value. If the function returns none,
# this part can be omitted
# Raises:
# Possible anomalies


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
# In the PY file, if all are classes, the top information format is as above,
# description fills in the description information, class fills in the class name,
# uses three quotation marks, does not need#
# Class should have a document string under its definition that describes
# the class
# If your class has attributes,
# Then there should be an attribute section in the document
# And it should follow the same format as function parameters
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
