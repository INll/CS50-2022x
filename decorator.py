def decorator(func):
    def check_zero(a, b):
        if b == 0:
            print("Cannot divide by zero")
            return
        return func(a, b)
    return check_zero

@decorator
def div(a, b):
    return a / b

print(div(2, 3))