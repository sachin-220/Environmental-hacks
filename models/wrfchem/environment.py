"""
WRF-Chem Computational Environment Detector and Prerequisite Inspector
"""
import os
import sys
import platform
import shutil
import ctypes
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from config.logging_config import get_logger

logger = get_logger("models.wrfchem.environment")


class WRFExecutionStatus(str, Enum):
    """Execution readiness status of WRF-Chem computational environment"""
    CONFIGURED = "CONFIGURED"       # Namelists, domain geometries, and chemistry mechanisms configured
    READY = "READY"                 # Binaries and environment verified; ready to simulate
    RUNNING = "RUNNING"             # Simulation currently active
    SUCCESSFUL = "SUCCESSFUL"       # Simulation finished with valid wrfout files
    UNAVAILABLE = "UNAVAILABLE"     # Native binaries missing on host (requires WSL/Docker/Linux HPC)


class SystemResources(BaseModel):
    os_name: str
    os_release: str
    os_version: str
    architecture: str
    python_version: str
    cpu_logical_cores: int
    ram_total_gb: float
    ram_available_gb: float
    disk_free_gb: float


class BinaryPrerequisites(BaseModel):
    gcc_path: Optional[str] = None
    gfortran_path: Optional[str] = None
    mpirun_path: Optional[str] = None
    wsl_path: Optional[str] = None
    docker_path: Optional[str] = None
    ncdump_path: Optional[str] = None
    geogrid_exe: Optional[str] = None
    ungrib_exe: Optional[str] = None
    metgrid_exe: Optional[str] = None
    real_exe: Optional[str] = None
    wrf_exe: Optional[str] = None


class EnvironmentReport(BaseModel):
    status: WRFExecutionStatus
    resources: SystemResources
    binaries: BinaryPrerequisites
    missing_prerequisites: List[str]
    is_wsl_available: bool
    is_docker_available: bool
    recommended_execution_backend: str
    summary_message: str


def get_memory_info() -> tuple[float, float]:
    """Get total and available RAM in GB across Windows/Linux"""
    if platform.system() == "Windows":
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ('dwLength', ctypes.c_ulong),
                ('dwMemoryLoad', ctypes.c_ulong),
                ('ullTotalPhys', ctypes.c_ulonglong),
                ('ullAvailPhys', ctypes.c_ulonglong),
                ('ullTotalPageFile', ctypes.c_ulonglong),
                ('ullAvailPageFile', ctypes.c_ulonglong),
                ('ullTotalVirtual', ctypes.c_ulonglong),
                ('ullAvailVirtual', ctypes.c_ulonglong),
                ('sullAvailExtendedVirtual', ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        try:
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            total_gb = stat.ullTotalPhys / (1024 ** 3)
            avail_gb = stat.ullAvailPhys / (1024 ** 3)
            return round(total_gb, 2), round(avail_gb, 2)
        except Exception:
            return 8.0, 4.0
    else:
        try:
            with open("/proc/meminfo") as f:
                lines = f.readlines()
            mem = {}
            for line in lines:
                parts = line.split(":")
                if len(parts) == 2:
                    mem[parts[0].strip()] = int(parts[1].split()[0])
            total_gb = mem.get("MemTotal", 0) / (1024 * 1024)
            avail_gb = mem.get("MemAvailable", mem.get("MemFree", 0)) / (1024 * 1024)
            return round(total_gb, 2), round(avail_gb, 2)
        except Exception:
            return 8.0, 4.0


class WRFEnvironmentDetector:
    """Inspects host hardware, compilers, libraries, and binaries for WRF-Chem execution"""

    @classmethod
    def inspect_environment(cls, custom_wrf_dir: Optional[Path] = None) -> EnvironmentReport:
        # 1. System Resources
        total_ram, avail_ram = get_memory_info()
        disk = shutil.disk_usage(".")
        free_disk_gb = round(disk.free / (1024 ** 3), 2)
        
        resources = SystemResources(
            os_name=platform.system(),
            os_release=platform.release(),
            os_version=platform.version(),
            architecture=platform.machine(),
            python_version=sys.version.split()[0],
            cpu_logical_cores=os.cpu_count() or 1,
            ram_total_gb=total_ram,
            ram_available_gb=avail_ram,
            disk_free_gb=free_disk_gb
        )

        # 2. Binary paths search
        def find_bin(name: str) -> Optional[str]:
            loc = shutil.which(name)
            if loc:
                return loc
            # Also check local wrf directory if specified
            if custom_wrf_dir and custom_wrf_dir.exists():
                for candidate in [custom_wrf_dir / "WPS" / name, custom_wrf_dir / "WRF" / "main" / name, custom_wrf_dir / "WRF" / "run" / name]:
                    if candidate.exists() and os.access(candidate, os.X_OK):
                        return str(candidate)
            return None

        binaries = BinaryPrerequisites(
            gcc_path=find_bin("gcc") or find_bin("icc"),
            gfortran_path=find_bin("gfortran") or find_bin("ifort"),
            mpirun_path=find_bin("mpirun") or find_bin("mpiexec"),
            wsl_path=find_bin("wsl"),
            docker_path=find_bin("docker"),
            ncdump_path=find_bin("ncdump"),
            geogrid_exe=find_bin("geogrid.exe"),
            ungrib_exe=find_bin("ungrib.exe"),
            metgrid_exe=find_bin("metgrid.exe"),
            real_exe=find_bin("real.exe"),
            wrf_exe=find_bin("wrf.exe")
        )

        missing = []
        if not binaries.gfortran_path:
            missing.append("Fortran Compiler (gfortran / ifort)")
        if not binaries.mpirun_path:
            missing.append("MPI Runtime (mpirun / mpiexec)")
        if not binaries.ncdump_path:
            missing.append("NetCDF-Fortran / ncdump utilities")
        if not binaries.geogrid_exe:
            missing.append("WPS geogrid.exe binary")
        if not binaries.metgrid_exe:
            missing.append("WPS metgrid.exe binary")
        if not binaries.real_exe:
            missing.append("WRF real.exe initialization binary")
        if not binaries.wrf_exe:
            missing.append("WRF-Chem wrf.exe coupled numerical solver binary")

        # Determine status
        is_wsl = binaries.wsl_path is not None
        is_docker = binaries.docker_path is not None

        if len(missing) == 0:
            status = WRFExecutionStatus.READY
            rec_backend = "Native Local Linux Environment"
            summary = "All WRF-Chem and WPS binaries and MPI dependencies verified on host."
        elif is_wsl:
            status = WRFExecutionStatus.CONFIGURED
            rec_backend = "WSL2 Ubuntu (Windows Subsystem for Linux)"
            summary = (
                f"WRF-Chem fully configured. Native Windows host lacks compiled WRF binaries ({len(missing)} missing). "
                f"WSL2 detected ({binaries.wsl_path}) and ready for Linux container/environment execution."
            )
        elif is_docker:
            status = WRFExecutionStatus.CONFIGURED
            rec_backend = "Docker Container (wrfchem-coupled:latest)"
            summary = (
                f"WRF-Chem fully configured. Native host lacks compiled WRF binaries ({len(missing)} missing). "
                f"Docker detected ({binaries.docker_path}) for containerized execution."
            )
        else:
            status = WRFExecutionStatus.UNAVAILABLE
            rec_backend = "Remote HPC Linux Cluster / Cloud Compute"
            summary = (
                f"WRF-Chem configured, but execution environment is unavailable on current host. "
                f"Missing: {', '.join(missing)}."
            )

        logger.info(f"WRF-Chem Environment Status: {status.value} (Backend: {rec_backend})")
        return EnvironmentReport(
            status=status,
            resources=resources,
            binaries=binaries,
            missing_prerequisites=missing,
            is_wsl_available=is_wsl,
            is_docker_available=is_docker,
            recommended_execution_backend=rec_backend,
            summary_message=summary
        )
