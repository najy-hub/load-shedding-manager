import json
import os
import sys
from datetime import datetime, date

# إضافة المسار إلى نظام Python
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from src.core.load_manager import LoadSheddingManager
    from src.models.models import TimeSlot, ReportType
    print("✓ تم تحميل المكتبات بنجاح")
except ImportError as e:
    print(f"❌ خطأ في تحميل المكتبات: {e}")
    print("🔍 جاري التحقق من الملفات...")
    
    # التحقق من وجود الملفات
    files_to_check = [
        'src/__init__.py',
        'src/core/__init__.py', 
        'src/core/load_manager.py',
        'src/models/__init__.py',
        'src/models/models.py'
    ]
    
    for file in files_to_check:
        if os.path.exists(file):
            print(f"✅ موجود: {file}")
        else:
            print(f"❌ مفقود: {file}")
    
    sys.exit(1)

def main():
    print("🚀 بدء تشغيل نظام إدارة الأحمال...")
    manager = LoadSheddingManager()
    
    while True:
        print("\n" + "="*50)
        print("نظام إدارة تخفيف الأحمال الكهربائية")
        print("="*50)
        print("1. حساب خطة التخفيف")
        print("2. عرض إحصائيات الخط")
        print("3. التقارير المتقدمة")
        print("4. تعيين سعة الخط")
        print("5. تفعيل/تعطيل خط")
        print("6. حفظ البيانات")
        print("7. خروج")
        
        try:
            choice = input("\nاختر الخيار: ").strip()
            
            if choice == '1':
                calculate_shedding_plan(manager)
            elif choice == '2':
                show_line_stats(manager)
            elif choice == '3':
                show_reports_menu(manager)
            elif choice == '4':
                set_line_capacity(manager)
            elif choice == '5':
                toggle_line_status(manager)
            elif choice == '6':
                manager.save_data('data/load_data.json')
                print("✓ تم حفظ البيانات")
            elif choice == '7':
                manager.save_data('data/load_data.json')
                print("✓ تم حفظ البيانات والخروج")
                break
            else:
                print("❌ خيار غير صحيح")
        except KeyboardInterrupt:
            print("\n\n⚠️ تم إيقاف البرنامج بواسطة المستخدم")
            break
        except Exception as e:
            print(f"❌ حدث خطأ: {e}")

def calculate_shedding_plan(manager):
    """حساب خطة التخفيف"""
    try:
        reduction = float(input("أدخل الحمل المطلوب تخفيفه (MW): "))
        time_slot = input("أدخل الفترة (morning/evening): ").strip().lower()
        
        if time_slot not in ['morning', 'evening']:
            print("❌ الفترة يجب أن تكون morning أو evening")
            return
        
        time_slot_enum = TimeSlot.MORNING if time_slot == 'morning' else TimeSlot.EVENING
        target_date = input("أدخل التاريخ (YYYY-MM-DD) أو اتركه فارغاً لليوم: ").strip()
        
        if target_date:
            target_date = date.fromisoformat(target_date)
        else:
            target_date = date.today()
        
        plan = manager.calculate_fair_shedding(reduction, time_slot_enum, target_date)
        
        print(f"\n📋 خطة التخفيف ليوم {target_date} - الفترة {time_slot}:")
        print("-" * 60)
        total_reduction = 0
        total_hours = 0
        
        for item in plan:
            print(f"الخط {item['line_id']:2d} ({item['line_name']}): "
                  f"{item['duration_hours']:5.2f} ساعة - "
                  f"{item['load_reduced_mw']:5.2f} MW")
            total_reduction += item['load_reduced_mw']
            total_hours += item['duration_hours']
        
        print("-" * 60)
        print(f"المجموع: {total_reduction:.2f} MW تخفيض - {total_hours:.2f} ساعة")
        
    except ValueError as e:
        print(f"❌ خطأ في الإدخال: {e}")
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")

def show_line_stats(manager):
    """عرض إحصائيات الخط"""
    try:
        line_id = int(input("أدخل رقم الخط (1-20): "))
        if 1 <= line_id <= 20:
            stats = manager.get_line_stats(line_id)
            if stats:
                print(f"\n📊 إحصائيات الخط {line_id}:")
                print(f"• إجمالي ساعات الفصل: {stats['total_hours']} ساعة")
                print(f"• ساعات الفصل لهذا الشهر: {stats['current_month_hours']} ساعة")
                print(f"• آخر فصل: {stats['last_shedding']}")
                
                if stats['monthly_breakdown']:
                    print("• تفصيل شهري:")
                    for month_key, hours in stats['monthly_breakdown'].items():
                        print(f"  - {month_key}: {hours} ساعة")
        else:
            print("❌ رقم الخط يجب أن يكون بين 1 و 20")
    except ValueError:
        print("❌ أدخل رقم صحيح")
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")

def show_reports_menu(manager):
    """قائمة التقارير"""
    while True:
        print("\n" + "="*50)
        print("📊 نظام التقارير المتقدم")
        print("="*50)
        print("1. تقرير يومي")
        print("2. تقرير أسبوعي")
        print("3. تقرير شهري")
        print("4. تقرير لفترة مخصصة")
        print("5. تصدير التقرير إلى ملف")
        print("6. العودة للقائمة الرئيسية")
        
        try:
            choice = input("\nاختر نوع التقرير: ").strip()
            
            if choice == '1':
                generate_daily_report(manager)
            elif choice == '2':
                generate_weekly_report(manager)
            elif choice == '3':
                generate_monthly_report(manager)
            elif choice == '4':
                generate_custom_report(manager)
            elif choice == '5':
                export_report_to_file_menu(manager)
            elif choice == '6':
                break
            else:
                print("❌ خيار غير صحيح")
        except Exception as e:
            print(f"❌ خطأ: {e}")

def generate_daily_report(manager):
    """تقرير يومي"""
    try:
        date_input = input("أدخل التاريخ (YYYY-MM-DD) أو اتركه فارغاً لليوم: ").strip()
        if date_input:
            target_date = date.fromisoformat(date_input)
        else:
            target_date = date.today()
        
        report = manager.generate_daily_report(target_date)
        display_report(report)
        
    except ValueError as e:
        print(f"❌ خطأ في التاريخ: {e}")
    except Exception as e:
        print(f"❌ خطأ في إنشاء التقرير: {e}")

def generate_weekly_report(manager):
    """تقرير أسبوعي"""
    try:
        date_input = input("أدخل تاريخ في الأسبوع المطلوب (YYYY-MM-DD) أو اتركه فارغاً للأسبوع الحالي: ").strip()
        if date_input:
            target_date = date.fromisoformat(date_input)
        else:
            target_date = date.today()
        
        report = manager.generate_weekly_report(target_date)
        display_report(report)
        
    except ValueError as e:
        print(f"❌ خطأ في التاريخ: {e}")
    except Exception as e:
        print(f"❌ خطأ في إنشاء التقرير: {e}")

def generate_monthly_report(manager):
    """تقرير شهري"""
    try:
        month_input = input("أدخل الشهر (1-12) أو اتركه فارغاً للشهر الحالي: ").strip()
        year_input = input("أدخل السنة أو اتركه فارغاً للسنة الحالية: ").strip()
        
        month = int(month_input) if month_input else date.today().month
        year = int(year_input) if year_input else date.today().year
        
        report = manager.generate_monthly_report(month, year)
        display_report(report)
        
    except ValueError as e:
        print(f"❌ خطأ في الإدخال: {e}")
    except Exception as e:
        print(f"❌ خطأ في إنشاء التقرير: {e}")

def generate_custom_report(manager):
    """تقرير لفترة مخصصة"""
    try:
        start_date = date.fromisoformat(input("أدخل تاريخ البداية (YYYY-MM-DD): ").strip())
        end_date = date.fromisoformat(input("أدخل تاريخ النهاية (YYYY-MM-DD): ").strip())
        
        if start_date > end_date:
            print("❌ تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
            return
        
        report = manager.generate_period_report(start_date, end_date)
        display_report(report)
        
    except ValueError as e:
        print(f"❌ خطأ في التاريخ: {e}")
    except Exception as e:
        print(f"❌ خطأ في إنشاء التقرير: {e}")

def display_report(report):
    """عرض التقرير"""
    try:
        print(f"\n{'='*60}")
        print(f"📈 تقرير {report.report_type.value}")
        print(f"📅 الفترة: {report.start_date} إلى {report.end_date}")
        print(f"{'='*60}")
        
        print(f"\n📊 الإحصائيات العامة:")
        print(f"• إجمالي ساعات الفصل: {report.total_hours} ساعة")
        print(f"• إجمالي الحمل المخفف: {report.total_reduction} MW")
        
        days_count = (report.end_date - report.start_date).days + 1
        print(f"• متوسط الساعات اليومية: {round(report.total_hours / max(1, days_count), 2)} ساعة")
        
        print(f"\n👥 إحصائيات المجموعات:")
        for group_id, stats in report.group_statistics.items():
            group_name = "المجموعة 1 (صباحي)" if group_id == 0 else "المجموعة 2 (مسائي)"
            print(f"  {group_name}:")
            print(f"    • ساعات الفصل: {stats['total_hours']} ساعة")
            print(f"    • الحمل المخفف: {stats['total_reduction']} MW")
            print(f"    • متوسط لكل خط: {stats['average_per_line']} ساعة")
        
        print(f"\n📋 إحصائيات الخطوط (الـ 5 الأكثر فصلًا):")
        # ترتيب الخطوط حسب ساعات الفصل
        sorted_lines = sorted(
            report.line_statistics.items(),
            key=lambda x: x[1]['total_hours'],
            reverse=True
        )[:5]
        
        for line_id, stats in sorted_lines:
            if stats['total_hours'] > 0:
                print(f"  الخط {line_id:2d} ({stats['line_name']}):")
                print(f"    • ساعات الفصل: {stats['total_hours']} ساعة")
                print(f"    • عدد مرات الفصل: {stats['shedding_count']} مرة")
                print(f"    • متوسط مدة الفصل: {stats['average_duration']} ساعة")
        
        print(f"\n📅 التفصيل اليومي:")
        for day, day_stats in sorted(report.daily_breakdown.items()):
            if day_stats['total_hours'] > 0:
                print(f"  {day}: {day_stats['total_hours']} ساعة - {day_stats['total_reduction']} MW")
                
    except Exception as e:
        print(f"❌ خطأ في عرض التقرير: {e}")

def export_report_to_file_menu(manager):
    """تصدير التقرير إلى ملف"""
    try:
        print("\n📤 تصدير التقرير إلى ملف")
        start_date = date.fromisoformat(input("أدخل تاريخ البداية (YYYY-MM-DD): ").strip())
        end_date = date.fromisoformat(input("أدخل تاريخ النهاية (YYYY-MM-DD): ").strip())
        
        report = manager.generate_period_report(start_date, end_date)
        filename = manager.export_report_to_file(report)
        print(f"✅ تم تصدير التقرير إلى: {filename}")
            
    except Exception as e:
        print(f"❌ خطأ في التصدير: {e}")

def set_line_capacity(manager):
    """تعيين سعة الخط"""
    try:
        line_id = int(input("أدخل رقم الخط (1-20): "))
        capacity = float(input("أدخل السعة (MW): "))
        
        manager.set_line_capacity(line_id, capacity)
        print(f"✓ تم تعيين سعة الخط {line_id} إلى {capacity} MW")
        
    except ValueError:
        print("❌ أدخل أرقام صحيحة")
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")

def toggle_line_status(manager):
    """تفعيل/تعطيل خط"""
    try:
        line_id = int(input("أدخل رقم الخط (1-20): "))
        status = input("تفعيل الخط؟ (y/n): ").strip().lower()
        
        is_active = status == 'y'
        manager.toggle_line_status(line_id, is_active)
        status_text = "مفعل" if is_active else "معطل"
        print(f"✓ تم {status_text} الخط {line_id}")
        
    except ValueError:
        print("❌ أدخل رقم صحيح")
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")

if __name__ == "__main__":
    main()
