import random
import time
import multiprocessing
import os
import csv
import matplotlib.pyplot as plt


# ----------------------------
# Funkcje do sortowania
# ----------------------------

def generate_files(num_files=120, values_per_file=1000, file_prefix="dane_"):

    for i in range(num_files):
        filename = f"{file_prefix}{i}.txt"
        values = [str(random.randint(-5000, 5000)) for _ in range(values_per_file)]
        with open(filename, "w") as f:
            f.write("\n".join(values))


def bubble_sort(data):

    n = len(data)
    for i in range(n - 1):
        for j in range(n - i - 1):
            if data[j] > data[j + 1]:
                data[j], data[j + 1] = data[j + 1], data[j]
    return data


def sort_file_faster(filename, repeat=10):

    with open(filename, "r") as f:
        data = list(map(int, f.read().split()))

    for _ in range(repeat):
        data = bubble_sort(data)



def sort_files_chunk(file_list, repeat=10):

    for f in file_list:
        sort_file_faster(f, repeat=repeat)


# ----------------------------
# Definicje scenariuszy
# ----------------------------

def scenario_1_chunk(files):
    # 1 proces: wszystkie 120 plików
    return [files]


def scenario_2_chunks(files):
    # 2 procesy: 60/60
    return [files[:60], files[60:]]


def scenario_3_chunks(files):
    # 3 procesy: 40/40/40
    return [files[:40], files[40:80], files[80:]]


def scenario_4_chunks(files):
    # 4 procesy: 30/30/30/30
    return [files[:30], files[30:60], files[60:90], files[90:]]


# ----------------------------
# Funkcje do uruchamiania scenariuszy
# ----------------------------

def run_scenario(chunks, repeat):

    num_procs = len(chunks)
    start = time.perf_counter()
    with multiprocessing.Pool(num_procs) as pool:

        pool.starmap(sort_files_chunk, [(c, repeat) for c in chunks])
    end = time.perf_counter()
    return end - start


# ----------------------------
# Funkcje do obliczania speedup
# ----------------------------

def get_time_for_scenario(results, scenario_name, size, repeat):

    for row in results:
        if (row["scenario_name"] == scenario_name
            and row["size"] == size
            and row["repeat"] == repeat):
            return row["time_s"]
    return None


def plot_speedup_for_params(results, size, repeat):
    # Nazwy scenariuszy
    scenario_1 = "Scenario 1 (1 proc)"
    scenario_2 = "Scenario 2 (2 procs)"
    scenario_3 = "Scenario 3 (3 procs)"
    scenario_4 = "Scenario 4 (4 procs)"


    t1 = get_time_for_scenario(results, scenario_1, size, repeat)
    t2 = get_time_for_scenario(results, scenario_2, size, repeat)
    t3 = get_time_for_scenario(results, scenario_3, size, repeat)
    t4 = get_time_for_scenario(results, scenario_4, size, repeat)

    if not all([t1, t2, t3, t4]):
        print(f"[BŁĄD] Nie znaleziono wszystkich czasów dla size={size}, repeat={repeat}")
        return

    # Obliczamy speedupy: T1 / Tn
    speedup_2 = t1 / t2
    speedup_3 = t1 / t3
    speedup_4 = t1 / t4


    scenarios = ["2 procs", "3 procs", "4 procs"]
    speedups = [speedup_2, speedup_3, speedup_4]

    plt.figure(figsize=(6, 4))
    plt.bar(scenarios, speedups, color=["green", "blue", "orange"])
    plt.title(f"Speedup dla size={size}, repeat={repeat} (wzgl. 1-proc)")
    plt.ylabel("Przyśpieszenie (T1 / Tn)")
    plt.ylim(0, max(speedups) + 0.5)

    for i, v in enumerate(speedups):
        plt.text(i, v + 0.02, f"{v:.2f}", ha='center', color='black', fontweight='bold')

    plt.tight_layout()
    plt.show()


def load_results_from_csv(csv_filename):
    loaded = []
    with open(csv_filename, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:

            loaded.append({
                "size": int(row["size"]),
                "repeat": int(row["repeat"]),
                "scenario_name": row["scenario_name"],
                "time_s": float(row["time_s"]),
                "chunks": row["chunks"]
            })
    return loaded


# ----------------------------
# Główny blok wykonawczy
# ----------------------------

if __name__ == "__main__":
    print("Aktualny katalog roboczy:", os.getcwd())


    sizes = [1000]
    repeats = [1]

    # Definicje scenariuszy
    scenario_defs = {
        "Scenario 1 (1 proc)": scenario_1_chunk,
        "Scenario 2 (2 procs)": scenario_2_chunks,
        "Scenario 3 (3 procs)": scenario_3_chunks,
        "Scenario 4 (4 procs)": scenario_4_chunks
    }


    results = []

    # -------------------------------
    # Pętla po różnych rozmiarach
    # -------------------------------
    for size in sizes:
        file_prefix = f"dane_{size}_"
        print(f"\n=== Generuję pliki: size={size} ===")
        generate_files(num_files=120, values_per_file=size, file_prefix=file_prefix)

        files_list = [f"{file_prefix}{i}.txt" for i in range(120)]

        print(f"--- ANALIZA dla plików: size={size} ---")

        # -------------------------------
        # Pętla po różnych repeat
        # -------------------------------
        for r in repeats:
            print(f"\n*** repeat={r} ***")

            # -------------------------------
            # Pętla po scenariuszach
            # -------------------------------
            for scenario_name, chunk_func in scenario_defs.items():
                chunks = chunk_func(files_list)
                elapsed = run_scenario(chunks, repeat=r)
                print(f"{scenario_name} => Time: {elapsed:.2f} s")


                row = {
                    "size": size,
                    "repeat": r,
                    "scenario_name": scenario_name,
                    "time_s": elapsed,

                    "chunks": str([len(ch) for ch in chunks])
                }
                results.append(row)

    # ===========================================================
    # 1) Zapisywanie do pliku CSV
    # ===========================================================
    csv_filename = "analysis_results.csv"
    fieldnames = ["size", "repeat", "scenario_name", "time_s", "chunks"]
    with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(results)

    print(f"\nWyniki zapisane do pliku: {csv_filename}")

    # ===========================================================
    # 2) Generowanie wykresów przyśpieszeń
    # ===========================================================



    unique_sizes = sorted(set(row["size"] for row in results))
    unique_repeats = sorted(set(row["repeat"] for row in results))

    for sz in unique_sizes:
        for r in unique_repeats:
            print(f"Rysuję speedup dla size={sz}, repeat={r}")
            plot_speedup_for_params(results, size=sz, repeat=r)



