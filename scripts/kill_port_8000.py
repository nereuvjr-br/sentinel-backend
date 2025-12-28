
import os
import subprocess
import re

def kill_process_on_port(port):
    try:
        # Netstat para achar PID
        output = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True).decode()
        pids = set()
        for line in output.splitlines():
            if "LISTENING" in line:
                parts = line.split()
                pid = parts[-1]
                pids.add(pid)
        
        if not pids:
            print(f"Nenhum processo ouvindo na porta {port}")
            return

        for pid in pids:
            if pid != "0":
                print(f"Matando processo {pid} na porta {port}...")
                subprocess.run(f"taskkill /F /PID {pid}", shell=True)

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    kill_process_on_port(8000)
