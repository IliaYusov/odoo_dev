a = 1
b = 1
i = 2
n = 9
fibonacci_list = [1,1]
while i < n:

    b, a = a + b, b
    fibonacci_list.append(b)
    i += 1
    print(i)
print(fibonacci_list)