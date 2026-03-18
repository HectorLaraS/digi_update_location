import os
import time
import subprocess

import win32event
import win32service
import win32serviceutil
import servicemanager

PROJECT_ROOT = r"D:\PythonGeneral\proyectos\digi_update_location"
PYTHON_EXE = os.path.join(PROJECT_ROOT, ".venv", "Scripts", "python.exe")

LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
STDOUT_LOG = os.path.join(LOG_DIR, "service_stdout.log")
STDERR_LOG = os.path.join(LOG_DIR, "service_stderr.log")
TRACE_LOG = os.path.join(LOG_DIR, "service_trace.log")

APP_ARGS = [PYTHON_EXE, "-m", "src.web.app"]


# ------------------------------------------------------------
# TRACE ULTRA BÁSICO (independiente de logging de Python)
# ------------------------------------------------------------
def write_trace(message: str) -> None:
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(TRACE_LOG, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {message}\n")
    except Exception:
        pass


# ------------------------------------------------------------
# SERVICIO
# ------------------------------------------------------------
class DigiManagerService(win32serviceutil.ServiceFramework):
    _svc_name_ = "DigiUpdateLocation"
    _svc_display_name_ = "Digi Update Location Service"
    _svc_description_ = "Digi Update Location 24/7 runner (pywin32)"

    def __init__(self, args):
        super().__init__(args)
        write_trace("Service __init__ called")
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.proc = None

    # --------------------------------------------------------
    # STOP
    # --------------------------------------------------------
    def SvcStop(self):
        write_trace("SvcStop called")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)

        if self.proc and self.proc.poll() is None:
            write_trace("Terminating child process")
            try:
                self.proc.terminate()
                for _ in range(20):
                    if self.proc.poll() is not None:
                        break
                    time.sleep(0.25)

                if self.proc.poll() is None:
                    write_trace("Killing child process")
                    self.proc.kill()
            except Exception as e:
                write_trace(f"Error stopping child process: {e}")

    # --------------------------------------------------------
    # RUN
    # --------------------------------------------------------
    def SvcDoRun(self):
        write_trace("SvcDoRun entered")

        try:
            os.makedirs(LOG_DIR, exist_ok=True)
            write_trace("LOG_DIR ensured")

            os.chdir(PROJECT_ROOT)
            write_trace(f"Changed directory to: {PROJECT_ROOT}")

            servicemanager.LogInfoMsg("Digi Update Location service starting...")
            write_trace("Before SERVICE_RUNNING")

            # CRÍTICO: avisar a Windows que arrancó
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            write_trace("SERVICE_RUNNING reported")

            with open(STDOUT_LOG, "a", encoding="utf-8") as out, open(STDERR_LOG, "a", encoding="utf-8") as err:
                write_trace("Opened stdout/stderr logs")

                self.proc = subprocess.Popen(
                    APP_ARGS,
                    cwd=PROJECT_ROOT,
                    stdout=out,
                    stderr=err,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                write_trace(f"Started child process: {APP_ARGS}")

                # Loop principal del servicio
                while True:
                    rc = win32event.WaitForSingleObject(self.stop_event, 1000)

                    if rc == win32event.WAIT_OBJECT_0:
                        write_trace("Stop event received")
                        break

                    # Si el hijo muere, reiniciar
                    if self.proc.poll() is not None:
                        write_trace(
                            f"Child exited with code {self.proc.returncode}. Restarting..."
                        )

                        servicemanager.LogErrorMsg(
                            f"Child exited with code {self.proc.returncode}. Restarting..."
                        )

                        time.sleep(3)

                        self.proc = subprocess.Popen(
                            APP_ARGS,
                            cwd=PROJECT_ROOT,
                            stdout=out,
                            stderr=err,
                            creationflags=subprocess.CREATE_NO_WINDOW,
                        )
                        write_trace("Child restarted")

            servicemanager.LogInfoMsg("Digi Update Location service stopped.")
            write_trace("SvcDoRun finished normally")

        except Exception as exc:
            write_trace(f"SvcDoRun crashed: {exc}")
            servicemanager.LogErrorMsg(
                f"Digi Update Location service failed: {exc}"
            )
            raise


# ------------------------------------------------------------
# ENTRYPOINT
# ------------------------------------------------------------
if __name__ == "__main__":
    write_trace("HandleCommandLine invoked")
    win32serviceutil.HandleCommandLine(DigiManagerService)