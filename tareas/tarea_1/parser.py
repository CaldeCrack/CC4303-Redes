#!/usr/bin/python3

best_times: dict[int, dict[int, list[str]]] = {
	128: {
		1: [],
		3: [],
		20: [],
		100: []
	},
	1024: {
		1: [],
		3: [],
		20: [],
		100: []
	},
	8192: {
		1: [],
		3: [],
		20: [],
		100: []
	}
}


def match_size(line: str) -> int:
	match line:
		case "----- size:128 -----\n":
			return 128
		case "----- size:1024 -----\n":
			return 1024
		case "----- size:8192 -----\n":
			return 8192
		case _:
			return 0


def match_files(line: str) -> int:
	match line:
		case "- 1 archivo grande\n":
			return 1
		case "- 3 archivos grandes\n":
			return 3
		case "- 20 archivos medianos\n":
			return 20
		case "- 100 archivos pequeños\n":
			return 100
		case _:
			return 0


def milli_to_str(time: int) -> str:
	minutes: int = int(time // 60)
	seconds: float = round(time % 60.0, 3)
	return f"{minutes}m{seconds}s"


def str_to_milli(time: str) -> int:
	minutes, sec = time.strip()[:-1].split("m")
	return 60 * int(minutes) + float(sec)


def str_to_milli2(text: str):
	time, server = text.split("| ")
	server = server[-1]
	return str_to_milli(time), server


def milli_to_str2(tuple) -> str:
	time, server = tuple[0], tuple[1]
	return f"{milli_to_str(float(time)):9}| {server}"


def results(file: str) -> None:
	server: int = int(file[5])
	with open(file, "r", encoding="utf8") as f:
		size: int = 128
		amount: int = 1
		cumsum: float = 0.0
		n: int = 0
		line: str = f.readline()

		while line:
			if curr_file := match_files(line):
				amount = curr_file
			elif curr_size := match_size(line):
				size = curr_size
			elif "Tiempo:" in line:
				cumsum += str_to_milli(line.split()[-1])
				n += 1
			elif line == "\n" and n:
				best_times[size][amount].append(f"{milli_to_str(cumsum / n):9} | {server}")
				cumsum, n = 0.0, 0
			line: str = f.readline()
		best_times[size][amount].append(f"{milli_to_str(cumsum / n):9} | {server}")


results("time_2.txt")
results("time_4.txt")
results("time_5.txt")

def print_results(i: int) -> None:
	for size, value in best_times.items():
		print(f"buffer size: {size}")
		for amount, value_2 in value.items():
			print(f"file amount: {amount:3} | time: {value_2[i][:-4]:9}")
		print()
	print()

# Display results per server
print("- server_echo2.py")
print_results(0)
print("- server_echo4.py")
print_results(1)
print("- server_echo5.py")
print_results(2)

print("- Recommendation")
for size, value in best_times.items():
	print(f"buffer size: {size}")
	for amount, value_2 in value.items():
		min_value: str = milli_to_str2(min(map(str_to_milli2, value_2)))
		print(f"file amount: {amount:3} | time: {min_value[:-3]} | server: {min_value[-1]}")
	print()
