from services.reporting import Report


class ClusterMaintenance:
    def __init__(self, report: Report):
        self._report = report.get_sub_report("ClusterMaintenance", init_status="ComponentInitialized",
                                             default_status_level="NOTIFY")

    def start_maintenance_mode(self):
        self._report.set_status("MaintenanceModeON")

    def stop_maintenance_mode(self):
        self._report.set_status("MaintenanceModeOFF")
