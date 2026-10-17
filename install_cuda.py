import os
import sys
import time
import urllib.request
import subprocess

WHEEL_URL = "https://download.pytorch.org/whl/cu121/torch-2.5.1%2Bcu121-cp311-cp311-win_amd64.whl"
WHEEL_NAME = "torch-2.5.1+cu121-cp311-cp311-win_amd64.whl"
TOTAL_SIZE = 2449385544

def download_with_resume(url, filename, total_size):
    retries = 0
    max_retries = 50

    while retries < max_retries:
        downloaded = os.path.getsize(filename) if os.path.exists(filename) else 0

        if downloaded >= total_size:
            print(f"\n[OK] Wheel already downloaded: {filename} ({downloaded / 1024 / 1024:.1f} MB)")
            return True

        if downloaded > 0:
            print(f"\n-> Resuming download at {downloaded / 1024 / 1024:.1f} MB / {total_size / 1024 / 1024:.1f} MB...")
        else:
            print(f"\n-> Connecting to PyTorch server (Total size: {total_size / 1024 / 1024:.1f} MB)...")

        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        if downloaded > 0:
            req.add_header('Range', f'bytes={downloaded}-')

        try:
            with urllib.request.urlopen(req, timeout=30) as response, open(filename, 'ab') as out_file:
                chunk_size = 1024 * 1024 # 1 MB chunk
                last_time = time.time()
                bytes_since_last = 0

                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    bytes_since_last += len(chunk)

                    now = time.time()
                    if now - last_time >= 0.5:
                        speed_mb = (bytes_since_last / (now - last_time)) / (1024 * 1024)
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {downloaded / 1024 / 1024:7.1f} / {total_size / 1024 / 1024:.1f} MB ({percent:5.1f}%) | Speed: {speed_mb:4.1f} MB/s", end="", flush=True)
                        last_time = now
                        bytes_since_last = 0

            if os.path.getsize(filename) >= total_size:
                print(f"\n[OK] 100% Downloaded successfully: {filename}")
                return True

        except Exception as e:
            retries += 1
            print(f"\n[Notice] Connection interrupted ({e}). Reconnecting in 3 seconds (Attempt {retries}/{max_retries})...")
            time.sleep(3)

    return False

def main():
    print("=" * 65)
    print("CUDA ACCELERATION INSTALLER FOR NVIDIA GEFORCE GTX 1070")
    print("=" * 65)

    success = download_with_resume(WHEEL_URL, WHEEL_NAME, TOTAL_SIZE)
    if not success:
        print("[ERROR] Failed to download PyTorch CUDA wheel after multiple retries.")
        sys.exit(1)

    print("\n-> Installing PyTorch & Torchvision with CUDA into virtual environment...")
    cmd = [
        sys.executable, "-m", "pip", "install", WHEEL_NAME, "torchvision",
        "--index-url", "https://download.pytorch.org/whl/cu121",
        "--no-cache-dir", "--force-reinstall"
    ]
    res = subprocess.run(cmd)

    if os.path.exists(WHEEL_NAME):
        try:
            os.remove(WHEEL_NAME)
            print("-> Cleaned up installer package to free disk space.")
        except Exception:
            pass

    print("\n" + "=" * 65)
    print("VERIFYING HARDWARE ACCELERATION:")
    print("=" * 65)
    try:
        import torch
        print(f"CUDA Enabled:  {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"Active Device: {torch.cuda.get_device_name(0)}")
            print("\n[SUCCESS] Your NVIDIA GTX 1070 is now fully active for 10x-15x faster AI inference!")
        else:
            print("Active Device: CPU only")
    except Exception as e:
        print(f"Error checking torch: {e}")

if __name__ == "__main__":
    main()
