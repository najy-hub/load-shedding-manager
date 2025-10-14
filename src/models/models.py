from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from enum import Enum

class TimeSlot(Enum):
    MORNING = "morning"
    EVENING = "evening"

@dataclass
class LoadLine:
    id: int
    name: str
    group: int
    capacity_mw: float
    is_active: bool = True

@dataclass
class SheddingRecord:
    line_id: int
    date: date
    time_slot: TimeSlot
    duration_hours: float
    load_reduced_mw: float

@dataclass
class LoadSheddingStats:
    line_id: int
    total_hours: float
    monthly_hours: Dict[str, float]  # month_year -> hours
    last_shedding_time: Optional[datetime]
