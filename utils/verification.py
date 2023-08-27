from random import randrange


def generate_verification_code(num_digits=6):
    return str(randrange(1, 10**num_digits)).zfill(num_digits)
