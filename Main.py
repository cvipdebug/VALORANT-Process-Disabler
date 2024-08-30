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
                p.wait()
                print(f"Terminated process: {process_name}")
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        print(f"Error terminating process {process_name}: {e}")
        return False

def is_autostart_disabled(program_name):
    """Checks if the autostart program is already disabled."""
    paths = [
        r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
        r"SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Run"
    ]
    
    for path in paths:
        try:
            registry_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_READ)
            try:
                value, _ = winreg.QueryValueEx(registry_key, program_name)
                if value:
                    return False
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

    return True

def disable_autostart(program_name):
    """Disables an autostart program by removing its registry entry."""
    paths = [
        r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
        r"SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Run"
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

def is_service_disabled(service_name):
    """Checks if the service is already disabled."""
    service_path = r"SYSTEM\\CurrentControlSet\\Services\\{}".format(service_name)
    
    try:
        registry_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, service_path, 0, winreg.KEY_READ)
        try:
            start_value, _ = winreg.QueryValueEx(registry_key, "Start")
            if start_value == 4:
                return True
        except FileNotFoundError:
            pass
        finally:
            winreg.CloseKey(registry_key)
    except Exception as e:
        print(f"Error checking service {service_name}: {e}")
    
    return False

def disable_service(service_name):
    """Disables a Windows service by modifying its registry entry."""
    service_path = r"SYSTEM\\CurrentControlSet\\Services\\{}".format(service_name)
    
    try:
        registry_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, service_path, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(registry_key, "Start", 0, winreg.REG_DWORD, 4)
        new_value, _ = winreg.QueryValueEx(registry_key, "Start")
        winreg.CloseKey(registry_key)
        print(f"Disabled service: {service_name}. New Start value: {new_value}")
        return True
    except FileNotFoundError:
        print(f"Service registry entry for {service_name} not found.")
        return False
    except PermissionError:
        print("Permission error: Run this script as an administrator.")
        return False
    except Exception as e:
        print(f"Error disabling service {service_name}: {e}")
        return False

def main():
    """Main function to handle the script execution."""
    run_as_admin()
    
    print("Starting the process termination and registry modification script...\n")
    
    processes_running = {
        "RiotClientServices.exe": is_process_running("RiotClientServices.exe"),
        "RiotClientCrashHandler.exe": is_process_running("RiotClientCrashHandler.exe"),
        "vgtray.exe": is_process_running("vgtray.exe")
    }
    
   
    for proc, running in processes_running.items():
        status = "running" if running else "not running"
        print(f"{proc} is {status}.")
    
    if any(processes_running.values()):
        print("\nTerminating processes...")
        
        processes_terminated = all([
            terminate_process("RiotClientServices.exe"),
            terminate_process("RiotClientCrashHandler.exe"),
            terminate_process("vgtray.exe")
        ])
    else:
        print("No specified processes are running.")
        processes_terminated = True
    
    autostart_disabled = is_autostart_disabled("Riot Vanguard")
    
    if not autostart_disabled:
        print("\nDisabling autostart...")
        autostart_disabled = disable_autostart("Riot Vanguard")
    
    service_disabled = is_service_disabled("vgc")
    
    if not service_disabled:
        print("\nDisabling service...")
        service_disabled = disable_service("vgc")
    
    if processes_terminated and autostart_disabled and service_disabled:
        print("\nAll tasks completed successfully.")
    else:
        print("\nSome tasks encountered errors.")
    
    input("Press Enter to close...")

if __name__ == "__main__":
    main()
