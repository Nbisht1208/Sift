from sift.core.benchmark import Benchmark

def main():
    print("Running Reliability Exam...")
    runner = Benchmark(iterations=20)
    runner.run()

if __name__ == "__main__":
    main()