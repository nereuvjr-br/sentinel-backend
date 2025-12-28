
def check_env_integrity():
    with open('.env', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            print(f"L{i+1}: {repr(line)}")

if __name__ == "__main__":
    check_env_integrity()
