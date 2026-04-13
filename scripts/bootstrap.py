from pathlib import Path

DIRS = [
    "data/receipts",
    "data/runs",
    "data/logs",
    "app/templates",
    "app/static",
]

def main() -> None:
    for d in DIRS:
        Path(d).mkdir(parents=True, exist_ok=True)
        print(f"created: {d}")

if __name__ == "__main__":
    main()
