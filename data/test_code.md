# Prime Number Checker

This file contains a simple Python program to determine if a number is prime.

## Code

```python
def is_prime(n):
    """Return True if n is a prime number, else False."""
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def main():
    try:
        num = int(input("Enter a number: "))
        if is_prime(num):
            print(f"{num} is a prime number.")
        else:
            print(f"{num} is not a prime number.")
    except ValueError:
        print("Please enter a valid integer.")

if __name__ == "__main__":
    main()
```

## Explanation

- **is_prime function:**  
  Checks if the provided number is prime by testing divisibility up to its square root.
  
- **main function:**  
  Prompts the user for input, uses the `is_prime` function to check primality, and then prints the result.

Enjoy testing the code!