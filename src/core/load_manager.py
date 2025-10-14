import json
import heapq
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from collections import defaultdict
from ..models.models import *

class LoadSheddingManager:
    def __init__(self, total_lines=20, lines_per_group=10):
        self.total_lines = total_lines
        self.lines_per_group = lines_per_group
        self.lines: List[LoadLine] = []
        self.shedding_history: List[SheddingRecord] = []
        self.stats: Dict[int, LoadSheddingStats] = {}
        self.current_day_group = 0  # 0 or 1
        
        self._initialize_lines()
        self._initialize_stats()
    
    def _initialize_lines(self):
        """تهيئة الخطوط الكهربائية"""
        for i in range(self.total_lines):
            group = 0 if i < self.lines_per_group else 1
            line = LoadLine(
                id=i + 1,
                name=f"Line_{i+1:02d}",
                group=group,
                capacity_mw=10.0  # سعة افتراضية
            )
            self.lines.append(line)
    
    def _initialize_stats(self):
        """تهيئة الإحصائيات"""
        for line in self.lines:
            self.stats[line.id] = LoadSheddingStats(
                line_id=line.id,
                total_hours=0.0,
                monthly_hours={},
                last_shedding_time=None
            )
    
    def get_current_group_schedule(self, target_date: date = None) -> int:
        """تحديد المجموعة المقرر تخفيفها حسب التاريخ"""
        if target_date is None:
            target_date = date.today()
        
        # تبديل المجموعات يومياً
        days_since_start = (target_date - date(2024, 1, 1)).days
        return days_since_start % 2
    
    def calculate_fair_shedding(self, required_reduction_mw: float, 
                              time_slot: TimeSlot, 
                              target_date: date = None) -> List[Dict]:
        """
        حساب التخفيف العادل للأحمال
        """
        if target_date is None:
            target_date = date.today()
        
        current_group = self.get_current_group_schedule(target_date)
        
        # تصفية الخطوط المتاحة للمجموعة الحالية
        available_lines = [line for line in self.lines 
                          if line.group == current_group and line.is_active]
        
        if not available_lines:
            return []
        
        # ترتيب الخطوط حسب الأولوية (الأقل ساعات فصل)
        priority_queue = []
        for line in available_lines:
            stats = self.stats[line.id]
            monthly_key = f"{target_date.month}_{target_date.year}"
            monthly_hours = stats.monthly_hours.get(monthly_key, 0)
            
            # الأولوية للخطوط ذات ساعات الفصل الأقل
            priority = monthly_hours
            
            heapq.heappush(priority_queue, (priority, line))
        
        # توزيع الحمل المطلوب
        shedding_plan = []
        remaining_reduction = required_reduction_mw
        
        while remaining_reduction > 0 and priority_queue:
            priority, line = heapq.heappop(priority_queue)
            
            # حساب مدة الفصل بناءً على الحمل المطلوب
            line_capacity = min(remaining_reduction, line.capacity_mw)
            duration_hours = (line_capacity / line.capacity_mw) * 2  # 2 ساعة كحد أقصى
            
            if duration_hours > 0:
                shedding_plan.append({
                    'line_id': line.id,
                    'line_name': line.name,
                    'duration_hours': round(duration_hours, 2),
                    'load_reduced_mw': round(line_capacity, 2),
                    'time_slot': time_slot.value
                })
                
                remaining_reduction -= line_capacity
                
                # تحديث الإحصائيات
                self._update_shedding_stats(line.id, duration_hours, target_date, time_slot)
        
        return shedding_plan
    
    def _update_shedding_stats(self, line_id: int, duration_hours: float, 
                             target_date: date, time_slot: TimeSlot):
        """تحديث إحصائيات الفصل"""
        stats = self.stats[line_id]
        stats.total_hours += duration_hours
        
        monthly_key = f"{target_date.month}_{target_date.year}"
        stats.monthly_hours[monthly_key] = stats.monthly_hours.get(monthly_key, 0) + duration_hours
        stats.last_shedding_time = datetime.now()
        
        # تسجيل في السجل التاريخي
        record = SheddingRecord(
            line_id=line_id,
            date=target_date,
            time_slot=time_slot,
            duration_hours=duration_hours,
            load_reduced_mw=self.lines[line_id-1].capacity_mw
        )
        self.shedding_history.append(record)
    
    def get_line_stats(self, line_id: int) -> Dict:
        """الحصول على إحصائيات خط معين"""
        if line_id not in self.stats:
            return {}
        
        stats = self.stats[line_id]
        return {
            'line_id': line_id,
            'total_hours': round(stats.total_hours, 2),
            'current_month_hours': self.get_current_month_hours(line_id),
            'last_shedding': stats.last_shedding_time,
            'monthly_breakdown': stats.monthly_hours
        }
    
    def get_current_month_hours(self, line_id: int) -> float:
        """ساعات الفصل للشهر الحالي"""
        current_date = date.today()
        monthly_key = f"{current_date.month}_{current_date.year}"
        return self.stats[line_id].monthly_hours.get(monthly_key, 0)
    
    def get_monthly_report(self, month: int, year: int) -> Dict:
        """تقرير شهري مفصل"""
        monthly_key = f"{month}_{year}"
        total_hours = 0
        line_hours = {}
        
        for line_id, stats in self.stats.items():
            hours = stats.monthly_hours.get(monthly_key, 0)
            line_hours[line_id] = hours
            total_hours += hours
        
        return {
            'month': month,
            'year': year,
            'total_hours': round(total_hours, 2),
            'line_hours': line_hours,
            'average_per_line': round(total_hours / len(self.lines), 2) if self.lines else 0
        }
    
    def set_line_capacity(self, line_id: int, capacity_mw: float):
        """تعيين سعة الخط"""
        if 1 <= line_id <= len(self.lines):
            self.lines[line_id-1].capacity_mw = capacity_mw
    
    def toggle_line_status(self, line_id: int, is_active: bool):
        """تفعيل/تعطيل خط"""
        if 1 <= line_id <= len(self.lines):
            self.lines[line_id-1].is_active = is_active
    
    def save_data(self, filename: str):
        """حفظ البيانات"""
        data = {
            'lines': [
                {
                    'id': line.id,
                    'name': line.name,
                    'group': line.group,
                    'capacity_mw': line.capacity_mw,
                    'is_active': line.is_active
                }
                for line in self.lines
            ],
            'shedding_history': [
                {
                    'line_id': record.line_id,
                    'date': record.date.isoformat(),
                    'time_slot': record.time_slot.value,
                    'duration_hours': record.duration_hours,
                    'load_reduced_mw': record.load_reduced_mw
                }
                for record in self.shedding_history
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_data(self, filename: str):
        """تحميل البيانات"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # تحميل الخطوط
            self.lines = []
            for line_data in data['lines']:
                line = LoadLine(
                    id=line_data['id'],
                    name=line_data['name'],
                    group=line_data['group'],
                    capacity_mw=line_data['capacity_mw'],
                    is_active=line_data['is_active']
                )
                self.lines.append(line)
            
            # تحميل السجل التاريخي
            self.shedding_history = []
            for record_data in data['shedding_history']:
                record = SheddingRecord(
                    line_id=record_data['line_id'],
                    date=date.fromisoformat(record_data['date']),
                    time_slot=TimeSlot(record_data['time_slot']),
                    duration_hours=record_data['duration_hours'],
                    load_reduced_mw=record_data['load_reduced_mw']
                )
                self.shedding_history.append(record)
            
            # إعادة حساب الإحصائيات
            self._initialize_stats()
            for record in self.shedding_history:
                self._update_shedding_stats(
                    record.line_id, 
                    record.duration_hours, 
                    record.date, 
                    record.time_slot
                )
                
        except FileNotFoundError:
            print("File not found, starting with fresh data")
