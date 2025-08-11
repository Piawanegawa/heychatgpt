import sys
import time
import threading

if sys.platform != 'win32':  # pragma: no cover - not relevant on non-Windows
    raise ImportError('VoiceTriggerService is only available on Windows')

import servicemanager
import socket
import win32event
import win32service
import win32serviceutil


class VoiceTriggerService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'VoiceTriggerService'
    _svc_display_name_ = 'Voice Trigger Service'
    _svc_description_ = 'Service that runs a worker thread for voice triggers.'

    def __init__(self, args):
        super().__init__(args)
        socket.setdefaulttimeout(60)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.worker_stop = threading.Event()
        self.worker_thread: threading.Thread | None = None

    # Service control handlers -------------------------------------------------
    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STOPPED,
            (self._svc_name_, '')
        )

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.worker_stop.set()
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join()
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def SvcShutdown(self):  # Called for system shutdowns
        self.SvcStop()

    def SvcOther(self, control):
        if control == win32service.SERVICE_CONTROL_PARAMCHANGE:
            # Restart worker thread on parameter changes
            self.worker_stop.set()
            if self.worker_thread and self.worker_thread.is_alive():
                self.worker_thread.join()
            self.worker_stop.clear()
            self.worker_thread = threading.Thread(target=self._worker, daemon=True)
            self.worker_thread.start()

    # Worker thread -----------------------------------------------------------
    def _worker(self):
        while not self.worker_stop.is_set():
            time.sleep(1)


