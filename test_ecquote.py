import sys
import subprocess
from pathlib import Path

# Configuration
req_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
error_csv = Path("./ecquote_errors.csv")
success_csv = Path("./ecquote_results.csv")

# Find all .req files recursively
req_files = sorted(req_dir.rglob("**/*.req"))

if not req_files:
    print(f"No .req files found in {req_dir}")
    sys.exit(0)

print(f"Found {len(req_files)} files in {req_dir}\n")

# Create output directory if needed
error_csv.parent.mkdir(parents=True, exist_ok=True)

success_count = 0
error_count = 0

with open(success_csv, 'w') as success_f, open(error_csv, 'w') as error_f:
    error_f.write("file,error\n")

    for req_file in req_files:
        print(f"Processing: {req_file}")
        result = subprocess.run(
            ['ecquote', str(req_file)],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            success_f.write(result.stdout)
            success_count += 1
        else:
            error = result.stderr.split('\n')[0].replace('"', '""')
            error_f.write(f'"{req_file}","{error}"\n')
            error_count += 1

print(f"\nDone! Success: {success_count}, Errors: {error_count}")
print(f"Results saved to: {success_csv} and {error_csv}")