from main import get_analysis

import argparse

async def main():
    parser = argparse.ArgumentParser(description="Analyze documentation text")
    parser.add_argument("--file", help="Path to the file containing the documentation text")
    args = parser.parse_args()
    
    if args.file:
        try:
            with open(args.file, "r") as file:
                documentation = file.read()
                result = await get_analysis(documentation)
                print("Analysis Result:")
                print(result)
        except FileNotFoundError:
            print("File not found")
    else:
        print("Please provide the path to the file containing the documentation text using the --file argument")

import asyncio
if __name__ == "__main__":
    asyncio.run(main())
