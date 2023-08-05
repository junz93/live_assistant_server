from argon2 import PasswordHasher

password_hasher = PasswordHasher(
    time_cost=3, 
    memory_cost=24576,
    parallelism=2,
)