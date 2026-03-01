import sympy 


def randprime(low: int, high: int) -> int:
    prime = sympy.randprime(low, high)
    if not isinstance(prime, int):
        raise ValueError
    return prime

