import psutil
import winreg
import ctypes
import sys

def is_admin():
    """Check if the script is running with administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception as e:
        print(f"Error checking admin status: {e}")
        return False

def run_as_admin():
    """Relaunch the script with administrative privileges."""
    if is_admin():
        return
    
    script = sys.argv[0]
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    except Exception as e:
        print(f"Error relaunching script as admin: {e}")
    sys.exit()

def is_process_running(process_name):
    """Checks if a process is running by its name."""
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            return True
    return False

def terminate_process(process_name):
    """Terminates a process by its name."""
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == process_name:
                p = psutil.Process(proc.info['pid'])
                p.terminate()
                p.wait()  # Wait for the process to terminate
                print(f"Terminated process: {process_name}")
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        print(f"Error terminating process {process_name}: {e}")
        return False

def is_autostart_disabled(program_name):
    """Checks if the autostart program is already disabled."""
    paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"
    ]
    
    for path in paths:
        try:
            registry_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_READ)
            try:
                value, _ = winreg.QueryValueEx(registry_key, program_name)
                if value:
                    return False  # Entry exists, so it's not disabled
            except FileNotFoundError:
                pass
            finally:
                winreg.CloseKey(registry_key)
        except PermissionError:
            print("Permission error: Run this script as an administrator.")
            return False
        except Exception as e:
            print(f"Error checking autostart: {e}")
            return False

    return True  # Entry does not exist, so it's disabled

def disable_autostart(program_name):
    """Disables an autostart program by removing its registry entry."""
    paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"
    ]
    
    for path in paths:
        try:
            registry_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_WRITE)
            try:
                winreg.DeleteValue(registry_key, program_name)
                print(f"Disabled autostart for: {program_name}")
                winreg.CloseKey(registry_key)
                return True
            except FileNotFoundError:
                continue
            finally:
                winreg.CloseKey(registry_key)
        except PermissionError:
            print("Permission error: Run this script as an administrator.")
            return False
        except Exception as e:
            print(f"Error disabling autostart: {e}")
            return False
    
    print(f"Registry entry for {program_name} not found.")
    return False

def main():
    """Main function to handle the script execution."""
    run_as_admin()  # Ensure the script is running with admin privileges
    
    print("Starting the process termination and registry modification script...\n")
    
    # Check if processes are running
    processes_running = {
        "RiotClientServices.exe": is_process_running("RiotClientServices.exe"),
        "RiotClientCrashHandler.exe": is_process_running("RiotClientCrashHandler.exe"),
        "vgtray.exe": is_process_running("vgtray.exe")
    }
    
    # Print process status
    for proc, running in processes_running.items():
        status = "running" if running else "not running"
        print(f"{proc} is {status}.")
    
    if any(processes_running.values()):
        print("\nTerminating processes...")
        # Terminate the processes
        processes_terminated = all([
            terminate_process("RiotClientServices.exe"),
            terminate_process("RiotClientCrashHandler.exe"),
            terminate_process("vgtray.exe")
        ])
    else:
        print("No specified processes are running.")
        processes_terminated = True
    
    # Check if autostart is already disabled
    autostart_disabled = is_autostart_disabled("Riot Vanguard")
    
    if not autostart_disabled:
        print("\nDisabling autostart...")
        autostart_disabled = disable_autostart("Riot Vanguard")
    
    if processes_terminated and autostart_disabled:
        print("\nAll tasks completed successfully.")
    else:
        print("\nSome tasks encountered errors.")
    
    input("Press Enter to close...")

if __name__ == "__main__":
    main()
