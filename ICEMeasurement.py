from dataclasses import dataclass
from collections import deque

@dataclass
class ICEMeasurement:
    label: str
    data: deque
    file: str
    visible: bool