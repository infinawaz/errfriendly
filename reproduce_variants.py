import sys
import asyncio
import errfriendly
from functools import lru_cache

# Enable all features
errfriendly.install()
errfriendly.enable_audit()

def run_variant_1():
    print("\n--- Variant 1: Exception Chaining Misuse ---")
    def read_number():
        try:
            int("42a")
        except Exception as e:
            # ❌ Root cause suppressed (no 'from e')
            raise RuntimeError("Failed to initialize system")
    read_number()

def run_variant_2():
    print("\n--- Variant 2: Cached Exception ---")
    @lru_cache(maxsize=1)
    def get_value(x):
        if x == 0:
            raise ValueError("Invalid input")
        return 10 / x

    try:
        get_value(0)
    except Exception:
        pass

    print("Call 2 (Cached):")
    get_value(0)

def run_variant_3():
    print("\n--- Variant 3: Unicode Look-Alike ---")
    data = {
        "timeout": 30,
        "timeоut": 60,  # Cyrillic "о"
    }
    # This will likely work but produce weird results, OR KeyError if accessing wrong one
    # The snippet provided by user:
    # print(data["timeout"] + data["timeоut"])
    # This actually works and prints 90. It's a semantic bug, not a crash.
    # UNLESS strict typing/linting catches it.
    # To make it crash or show behavior, we'll assume the user meant to override but didn't.
    print(f"timeout: {data['timeout']}")
    print(f"timeоut: {data['timeоut']}") # Different keys!
    
    # Let's force a crash related to this confusion
    # e.g. Trying to access the one we think we set
    config = {"timeоut": 60} # Cyrillic set
    print(config["timeout"]) # Latin access -> KeyError

def run_variant_4():
    print("\n--- Variant 4: Mutable Default Argument ---")
    def add_item(item, bucket=[]):
        bucket.append(item)
        if len(bucket) > 2:
            raise ValueError("Too many items")
        return bucket

    print(add_item(1))
    print(add_item(2))
    print(add_item(3)) # Boom

def run_variant_5():
    print("\n--- Variant 5: Context Manager Hides Root ---")
    class Wrapper:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            # ❌ Swallows original exception, raises new one
            raise RuntimeError("Operation failed")

    with Wrapper():
        int("abc")

def run_variant_6():
    print("\n--- Variant 6: Wrong Exception Re-raise ---")
    def process():
        try:
            int("x")
        except Exception as e:
            raise e  # ❌ traceback reset (should be 'raise')
    process()

def run_variant_7():
    print("\n--- Variant 7: Async Exception Lost ---")
    async def worker():
        raise ValueError("Async failure")

    async def main():
        task = asyncio.create_task(worker())
        await asyncio.sleep(0.1)
        await task

    asyncio.run(main())

def run_variant_8():
    print("\n--- Variant 8: Semantic Bug (Average Empty) ---")
    def average(nums):
        return sum(nums) / len(nums)
    average([])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reproduce_variants.py <1-8>")
        sys.exit(1)
    
    variant = sys.argv[1]
    globals()[f"run_variant_{variant}"]()
