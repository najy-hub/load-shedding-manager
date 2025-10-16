import json
import heapq
import os
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
        self.current_day_group = 0
        
        self._initialize_with_data()
    
    def _initialize_with_data(self):
        """التهيئة مع تحميل البيانات أو إنشائها تلقائياً"""
        try:
            self.load_data('data/load_data.json')
            print("✓ تم تحميل بيانات الخطوط بنجاح")
        except FileNotFoundError:
            print("⚠️ لم يتم العثور على ملف البيانات، جاري الإنشاء التلقائي...")
            self.initialize_load_data()
            self.load_data('data/load_data.json')
        except Exception as e:
            print(f"❌ خطأ في تحميل البيانات: {e}")
            self._initialize_lines()
            self._initialize_stats()
    
    def initialize_load_data(self, filename: str = 'data/load_data.json'):
        """إنشاء ملف بيانات أولي للخطوط العشرين"""
        os.makedirs('data', exist_ok=True)
        
        initial_data = {
            'lines': [
                {
                    'id': i + 1,
                    'name': f"Line_{i+1:02d}",
                    'group': 0 if i < 10 else 1,
                    'capacity_mw': 10.0,
                    'is_active': True
                }
                for i in range(20)
            ],
            'shedding_history': []
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ تم إنشاء ملف البيانات الأولي بـ {len(initial_data['lines'])} خط")
    
    def _initialize_lines(self):
        """تهيئة الخطوط الكهربائية (بدون ملف)"""
        for i in range(self.total_lines):
            group = 0 if i < self.lines_per_group else 1
            line = LoadLine(
                id=i + 1,
                name=f"Line_{i+1:02d}",
                group=group,
                capacity_mw=10.0
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

    # ========== دوال التقارير الجديدة ==========

    def generate_period_report(self, start_date: date, end_date: date, report_type: ReportType = ReportType.CUSTOM) -> PeriodReport:
        """إنشاء تقرير لفترة محددة"""
        
        # تصفية السجلات ضمن الفترة المطلوبة
        period_records = [
            record for record in self.shedding_history
            if start_date <= record.date <= end_date
        ]
        
        # إحصائيات الخطوط
        line_stats = {}
        total_hours = 0
        total_reduction = 0
        
        for line in self.lines:
            line_records = [r for r in period_records if r.line_id == line.id]
            line_hours = sum(r.duration_hours for r in line_records)
            line_reduction = sum(r.load_reduced_mw for r in line_records)
            
            line_stats[line.id] = {
                'line_name': line.name,
                'group': line.group,
                'total_hours': round(line_hours, 2),
                'total_reduction': round(line_reduction, 2),
                'shedding_count': len(line_records),
                'average_duration': round(line_hours / len(line_records), 2) if line_records else 0
            }
            
            total_hours += line_hours
            total_reduction += line_reduction
        
        # إحصائيات المجموعات
        group_stats = {}
        for group_id in [0, 1]:
            group_lines = [line for line in self.lines if line.group == group_id]
            group_hours = sum(line_stats[line.id]['total_hours'] for line in group_lines)
            group_reduction = sum(line_stats[line.id]['total_reduction'] for line in group_lines)
            
            group_stats[group_id] = {
                'total_hours': round(group_hours, 2),
                'total_reduction': round(group_reduction, 2),
                'line_count': len(group_lines),
                'average_per_line': round(group_hours / len(group_lines), 2) if group_lines else 0
            }
        
        # تفصيل يومي
        daily_breakdown = {}
        current_date = start_date
        while current_date <= end_date:
            day_records = [r for r in period_records if r.date == current_date]
            day_hours = sum(r.duration_hours for r in day_records)
            day_reduction = sum(r.load_reduced_mw for r in day_records)
            
            daily_breakdown[current_date] = {
                'total_hours': round(day_hours, 2),
                'total_reduction': round(day_reduction, 2),
                'record_count': len(day_records)
            }
            current_date += timedelta(days=1)
        
        return PeriodReport(
            start_date=start_date,
            end_date=end_date,
            report_type=report_type,
            total_hours=round(total_hours, 2),
            total_reduction=round(total_reduction, 2),
            line_statistics=line_stats,
            group_statistics=group_stats,
            daily_breakdown=daily_breakdown
        )

    def generate_daily_report(self, target_date: date = None) -> PeriodReport:
        """تقرير يومي"""
        if target_date is None:
            target_date = date.today()
        
        return self.generate_period_report(target_date, target_date, ReportType.DAILY)

    def generate_weekly_report(self, target_date: date = None) -> PeriodReport:
        """تقرير أسبوعي"""
        if target_date is None:
            target_date = date.today()
        
        start_date = target_date - timedelta(days=target_date.weekday())
        end_date = start_date + timedelta(days=6)
        
        return self.generate_period_report(start_date, end_date, ReportType.WEEKLY)

    def generate_monthly_report(self, month: int = None, year: int = None) -> PeriodReport:
        """تقرير شهري"""
        if month is None:
            month = date.today().month
        if year is None:
            year = date.today().year
        
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        return self.generate_period_report(start_date, end_date, ReportType.MONTHLY)

    def export_report_to_file(self, report: PeriodReport, filename: str = None):
        """تصدير التقرير إلى ملف"""
        if filename is None:
            filename = f"report_{report.start_date}_{report.end_date}.json"
        
        report_data = {
            'report_info': {
                'start_date': report.start_date.isoformat(),
                'end_date': report.end_date.isoformat(),
                'report_type': report.report_type.value,
                'total_hours': report.total_hours,
                'total_reduction': report.total_reduction
            },
            'line_statistics': report.line_statistics,
            'group_statistics': report.group_statistics,
            'daily_breakdown': {
                date.isoformat(): data for date, data in report.daily_breakdown.items()
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        return filename

    # ========== نهاية دوال التقارير ==========

    def get_current_group_schedule(self, target_date: date = None) -> int:
        """تحديد المجموعة المقرر تخفيفها حسب التاريخ"""
        if target_date is None:
            target_date = date.today()
        
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
        
        available_lines = [line for line in self.lines 
                          if line.group == current_group and line.is_active]
        
        if not available_lines:
            return []
        
        priority_queue = []
        for line in available_lines:
            stats = self.stats[line.id]
            monthly_key = f"{target_date.month}_{target_date.year}"
            monthly_hours = stats.monthly_hours.get(monthly_key, 0)
            
            priority = (monthly_hours, line.id)
            
            heapq.heappush(priority_queue, (priority, line))
        
        shedding_plan = []
        remaining_reduction = required_reduction_mw
        
        while remaining_reduction > 0 and priority_queue:
            priority, line = heapq.heappop(priority_queue)
            
            line_capacity = min(remaining_reduction, line.capacity_mw)
            duration_hours = (line_capacity / line.capacity_mw) * 2
            
            if duration_hours > 0:
                shedding_plan.append({
                    'line_id': line.id,
                    'line_name': line.name,
                    'duration_hours': round(duration_hours, 2),
                    'load_reduced_mw': round(line_capacity, 2),
                    'time_slot': time_slot.value
                })
                
                remaining_reduction -= line_capacity
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
            
            self._initialize_stats()
            for record in self.shedding_history:
                self._update_shedding_stats(
                    record.line_id, 
                    record.duration_hours, 
                    record.date, 
                    record.time_slot
                )
                
        except FileNotFoundError:
            raise FileNotFoundError("لم يتم العثور على ملف البيانات")
        except Exception as e:
            raise Exception(f"خطأ في تحميل البيانات: {e}")
