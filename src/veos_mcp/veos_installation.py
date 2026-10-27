import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VeosInstallation:
    year: int
    release: str
    bin_path: Path
    source_name: str

    @property
    def schema_path(self) -> Path:
        return self.bin_path.parent / "tools" / "schemas"

    @property
    def veos_path(self) -> Path:
        return self.bin_path / "veos.exe" if sys.platform.startswith("win32") else self.bin_path / "veos"
