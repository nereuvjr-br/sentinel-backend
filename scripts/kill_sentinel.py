
import psutil
import sys

def kill_sentinel():
    killed = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any('start_sentinel.py' in arg for arg in cmdline):
                    print(f"Matando Daemon PID: {proc.info['pid']}")
                    proc.kill()
                    killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    print(f"Total de processos Sentinel mortos: {killed}")

if __name__ == "__main__":
    kill_sentinel()
