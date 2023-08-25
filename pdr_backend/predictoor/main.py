import sys
from pdr_backend.predictoor.approach1.main import main as main1
from pdr_backend.predictoor.approach2.main import main as main2

def main():
    if len(sys.argv) == 1:
        main1()
    else:
        arg = sys.argv[1]
        if arg == "1":
            main1()
        elif arg == "2":
            main2()
        else:
            print("Invalid argument. Use '1' for approach1 or '2' for approach2.")

if __name__ == "__main__":
    main()
