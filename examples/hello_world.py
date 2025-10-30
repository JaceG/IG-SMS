"""
Simple Hello World example
"""


def greet(name="World"):
    """Greet someone by name."""
    return f"Hello, {name}!"


if __name__ == "__main__":
    print(greet())
    print(greet("Python Developer"))


