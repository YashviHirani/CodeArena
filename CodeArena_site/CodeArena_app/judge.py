import subprocess
import tempfile
import os
import shutil
import time
import resource

# ======================
# UTIL: MEMORY TRACKING
# ======================

def get_memory_mb():
    """
    Approximate memory usage of current process (MB)
    """
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2)


# ======================
# MAIN ENTRY
# ======================

def judge_code(language, code, testcases):
    if language == "python":
        return judge_python(code, testcases)
    elif language == "java":
        return judge_java(code, testcases)
    else:
        return {
            "verdict": "Unsupported Language"
        }


# ======================
# PYTHON JUDGE
# ======================

def judge_python(code, testcases):

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        file_path = f.name

    try:
        start_time = time.perf_counter()

        for idx, tc in enumerate(testcases, start=1):
            try:
                result = subprocess.run(
                    ["python3", file_path],
                    input=tc.input_data.strip() + "\n",
                    text=True,
                    capture_output=True,
                    timeout=2
                )
            except subprocess.TimeoutExpired:
                return {
                    "verdict": "Time Limit Exceeded",
                    "failed_testcase": idx
                }

            if result.returncode != 0:
                return {
                    "verdict": "Runtime Error",
                    "failed_testcase": idx,
                    "error": result.stderr.strip()
                }

            output = result.stdout.strip()
            expected = tc.expected_output.strip()

            if output != expected:
                return {
                    "verdict": "Wrong Answer",
                    "failed_testcase": idx
                }

        end_time = time.perf_counter()

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    return {
        "verdict": "Accepted",
        "time_ms": round((end_time - start_time) * 1000, 2),
        "memory_mb": get_memory_mb()
    }


# ======================
# JAVA JUDGE
# ======================

def judge_java(code, testcases):

    if "class Main" not in code:
        return {
            "verdict": "Invalid Format: class Main required"
        }

    temp_dir = tempfile.mkdtemp()
    java_file = os.path.join(temp_dir, "Main.java")

    with open(java_file, "w") as f:
        f.write(code)

    try:
        # ------------------
        # COMPILE
        # ------------------
        compile_start = time.perf_counter()

        compile_res = subprocess.run(
            ["javac", java_file],
            capture_output=True,
            text=True,
            timeout=3
        )

        compile_end = time.perf_counter()

        if compile_res.returncode != 0:
            return {
                "verdict": "Compilation Error",
                "error": compile_res.stderr.strip()
            }

        # ------------------
        # RUN TESTCASES
        # ------------------
        run_start = time.perf_counter()

        for idx, tc in enumerate(testcases, start=1):
            try:
                run_res = subprocess.run(
                    ["java", "-cp", temp_dir, "Main"],
                    input=tc.input_data.strip() + "\n",
                    capture_output=True,
                    text=True,
                    timeout=2
                )
            except subprocess.TimeoutExpired:
                return {
                    "verdict": "Time Limit Exceeded",
                    "failed_testcase": idx
                }

            if run_res.returncode != 0:
                return {
                    "verdict": "Runtime Error",
                    "failed_testcase": idx,
                    "error": run_res.stderr.strip()
                }

            if run_res.stdout.strip() != tc.expected_output.strip():
                return {
                    "verdict": "Wrong Answer",
                    "failed_testcase": idx
                }

        run_end = time.perf_counter()

    finally:
        shutil.rmtree(temp_dir)

    return {
        "verdict": "Accepted",
        "time_ms": round((compile_end - compile_start + run_end - run_start) * 1000, 2),
        "memory_mb": get_memory_mb()
    }
