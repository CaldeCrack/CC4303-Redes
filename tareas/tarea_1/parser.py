#!/usr/bin/python3

best_times: dict[int, dict[int, str]] = {
	128: {
		1: "ñ",
		3: "ñ",
		20: "ñ",
		100: "ñ"
	},
	1024: {
		1: "ñ",
		3: "ñ",
		20: "ñ",
		100: "ñ"
	},
	8192: {
		1: "ñ",
		3: "ñ",
		20: "ñ",
		100: "ñ"
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


def results(file: str) -> None:
	server: int = int(file[5])
	with open(file, "r", encoding="utf8") as f:
		size: int = 128
		amount: int = 1
		line: str = f.readline()

		while line:
			if curr_file := match_files(line):
				amount = curr_file
			elif curr_size := match_size(line):
				size = curr_size
			elif "Tiempo:" in line:
				best_times[size][amount] = min(best_times[size][amount], f"{line.split()[-1]:9} | {server}")
			line: str = f.readline()


results("time_2.txt")
results("time_4.txt")
results("time_5.txt")
for key, value in best_times.items():
	print(f"{key:4}: {value}")
