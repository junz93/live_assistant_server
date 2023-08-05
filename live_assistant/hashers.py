from django.contrib.auth.hashers import Argon2PasswordHasher

class CustomArgon2PasswordHasher(Argon2PasswordHasher):
    time_cost = 3
    memory_cost = 24576
    parallelism = 2
