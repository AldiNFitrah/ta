import sys

from src.multiplier.multiplier import Multiplier


def main(count):
    for i in range(count):
        Multiplier(f"multiplier-{i}").start_consuming()


if __name__ == "__main__":
    instance_count = 1
    if len(sys.argv) > 1:
        instance_count = int(sys.argv[1])

    main(instance_count)
