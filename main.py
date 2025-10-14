import json
from datetime import datetime, date
from src.core.load_manager import LoadSheddingManager
from src.models.models import TimeSlot

def main():
    manager = LoadSheddingManager()
    
    # محاولة تحميل البيانات السابقة
    try:
        manager.load_data('data/load_data.json')
        print("✓ تم تحميل البيانات السابقة")
    except:
        print("✓ بدء نظام جديد")
    
    while True:
        print("\n" + "="*50)
        print("نظام إدارة تخفيف الأحمال الكهربائية")
        print("="*50)
        print("1. حساب خطة التخفيف")
        print("2. عرض إحصائيات الخط")
        print("3. تقرير شهري")
        print("4. تعيين سعة الخط")
        print("5. تفعيل/تعطيل خط")
        print("6. حفظ البيانات")
        print("7. خروج")
        
        choice = input("\nاختر الخيار: ").strip()
        
        if choice == '1':
            calculate_shedding_plan(manager)
        elif choice == '2':
            show_line_stats(manager)
        elif choice == '3':
            show_monthly_report(manager)
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

def show_monthly_report(manager):
    """عرض التقرير الشهري"""
    try:
        month = int(input("أدخل الشهر (1-12): "))
        year = int(input("أدخل السنة: "))
        
        report = manager.get_monthly_report(month, year)
        
        print(f"\n📈 التقرير الشهري لـ {month}/{year}:")
        print(f"• إجمالي ساعات الفصل: {report['total_hours']} ساعة")
        print(f"• متوسط الساعات لكل خط: {report['average_per_line']} ساعة")
        
        print("\n• ساعات الفصل لكل خط:")
        for line_id, hours in report['line_hours'].items():
            if hours > 0:
                print(f"  الخط {line_id:2d}: {hours:6.2f} ساعة")
                
    except ValueError:
        print("❌ أدخل أرقام صحيحة")

def set_line_capacity(manager):
    """تعيين سعة الخط"""
    try:
        line_id = int(input("أدخل رقم الخط (1-20): "))
        capacity = float(input("أدخل السعة (MW): "))
        
        manager.set_line_capacity(line_id, capacity)
        print(f"✓ تم تعيين سعة الخط {line_id} إلى {capacity} MW")
        
    except ValueError:
        print("❌ أدخل أرقام صحيحة")

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

if __name__ == "__main__":
    main()
