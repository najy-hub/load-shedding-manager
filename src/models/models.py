from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from enum import Enum

class TimeSlot(Enum):
    MORNING = "morning"
    EVENING = "evening"

class ReportType(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"

@dataclass
class LoadLine:
    id: int
    name: str
    group: int
    capacity_mw: float
    is_active: bool = True
    
    def __lt__(self, other):
        return self.id < other.id

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
    monthly_hours: Dict[str, float]
    last_shedding_time: Optional[datetime]

@dataclass
class PeriodReport:
    start_date: date
    end_date: date
    report_type: ReportType
    total_hours: float
    total_reduction: float
    line_statistics: Dict[int, Dict]
    group_statistics: Dict[int, Dict]
    daily_breakdown: Dict[date, Dict]
