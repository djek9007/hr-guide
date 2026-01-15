"""
Команда Django для создания тестовых данных.
Использование: python manage.py create_test_data
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from contacts.models import Department, Division, Position, Room, Contact


class Command(BaseCommand):
    help = 'Создает тестовые данные: департаменты, отделы, должности, кабинеты и сотрудников'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие данные перед созданием тестовых',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Очистка существующих данных...'))
            Contact.objects.all().delete()
            Division.objects.all().delete()
            Department.objects.all().delete()
            Room.objects.all().delete()
            Position.objects.all().delete()

        with transaction.atomic():
            # Создаем департаменты
            self.stdout.write('Создание департаментов...')
            
            dept_management = Department.objects.create(
                name_ru='Руководство',
                name_kk='Басшылық',
                type='management',
                display_order=1,
                description='Руководство министерства'
            )
            
            dept_audit = Department.objects.create(
                name_ru='Департамент внутреннего аудита',
                name_kk='Ішкі аудит департаменті',
                type='department',
                display_order=2,
                description='Департамент внутреннего аудита'
            )
            
            dept_planning = Department.objects.create(
                name_ru='Департамент анализа и стратегического планирования',
                name_kk='Талдау және стратегиялық жоспарлау департаменті',
                type='department',
                display_order=3,
                description='Департамент анализа и стратегического планирования'
            )
            
            dept_economics = Department.objects.create(
                name_ru='Департамент экономики и финансов',
                name_kk='Экономика және қаржы департаменті',
                type='department',
                display_order=4,
                description='Департамент экономики и финансов'
            )
            
            dept_law = Department.objects.create(
                name_ru='Юридический департамент',
                name_kk='Заң департаменті',
                type='department',
                display_order=5,
                description='Юридический департамент'
            )

            # Создаем отделы внутри департаментов
            self.stdout.write('Создание отделов...')
            
            # Отделы в Департаменте внутреннего аудита
            div_audit = Division.objects.create(
                department=dept_audit,
                name_ru='Управление аудита',
                name_kk='Аудит басқармасы',
                display_order=1
            )
            
            # Отделы в Департаменте анализа и стратегического планирования
            div_strategy = Division.objects.create(
                department=dept_planning,
                name_ru='Управление стратегического планирования',
                name_kk='Cтратегиялық жоспарлау басқармасы',
                display_order=1
            )
            
            div_analysis = Division.objects.create(
                department=dept_planning,
                name_ru='Управление сводного анализа',
                name_kk='Жиынтық талдау басқармасы',
                display_order=2
            )
            
            # Отделы в Департаменте экономики и финансов
            div_budget_planning = Division.objects.create(
                department=dept_economics,
                name_ru='Управление планирования бюджета',
                name_kk='Бюджетті жоспарлау басқармасы',
                display_order=1
            )
            
            div_accounting = Division.objects.create(
                department=dept_economics,
                name_ru='Управление бухгалтерского учета и отчетности',
                name_kk='Бухгалтерлік есеп және есептілік басқармасы',
                display_order=2
            )
            
            div_budget_execution = Division.objects.create(
                department=dept_economics,
                name_ru='Управление исполнения бюджета',
                name_kk='Бюджетті атқару басқармасы',
                display_order=3
            )
            
            # Отделы в Юридическом департаменте
            div_legal_expertise = Division.objects.create(
                department=dept_law,
                name_ru='Управление правовой экспертизы нормативных правовых актов',
                name_kk='Нормативтік құқықтық актілерді құқықтық сараптау басқармасы',
                display_order=1
            )
            
            div_legal_support = Division.objects.create(
                department=dept_law,
                name_ru='Управление правового обеспечения',
                name_kk='Құқықтық қамтамасыз ету басқармасы',
                display_order=2
            )
            
            # Секретариат (независимый отдел, может быть привязан к руководству)
            div_secretariat = Division.objects.create(
                department=dept_management,
                name_ru='Секретариат',
                name_kk='Хатшылық',
                display_order=1
            )

            # Создаем должности
            self.stdout.write('Создание должностей...')
            
            pos_minister = Position.objects.create(
                name_ru='Министр',
                name_kk='Министр'
            )
            
            pos_deputy = Position.objects.create(
                name_ru='Заместитель министра',
                name_kk='Министр орынбасары'
            )
            
            pos_advisor = Position.objects.create(
                name_ru='Советник министра',
                name_kk='Министрдің кеңесшісі'
            )
            
            pos_external_advisor = Position.objects.create(
                name_ru='Советник министра (внештатный)',
                name_kk='Министрдің штаттан тыс кеңесшісі'
            )
            
            pos_press_secretary = Position.objects.create(
                name_ru='Пресс-секретарь',
                name_kk='Баспасөз-хатшысы'
            )
            
            pos_director = Position.objects.create(
                name_ru='Директор департамента',
                name_kk='Департамент директоры'
            )
            
            pos_head = Position.objects.create(
                name_ru='Начальник управления',
                name_kk='Басқарма бастығы'
            )
            
            pos_specialist = Position.objects.create(
                name_ru='Главный специалист',
                name_kk='Бас маман'
            )
            
            pos_lead_specialist = Position.objects.create(
                name_ru='Ведущий специалист',
                name_kk='Жетекші маман'
            )

            # Создаем кабинеты
            self.stdout.write('Создание кабинетов...')
            
            room_751 = Room.objects.create(number='751', floor=7, building='Главный корпус')
            room_750 = Room.objects.create(number='750', floor=7, building='Главный корпус')
            room_755 = Room.objects.create(number='755', floor=7, building='Главный корпус')
            room_734 = Room.objects.create(number='734', floor=7, building='Главный корпус')
            room_740 = Room.objects.create(number='740', floor=7, building='Главный корпус')
            room_201 = Room.objects.create(number='201', floor=2, building='Главный корпус')
            room_302 = Room.objects.create(number='302', floor=3, building='Главный корпус')
            room_415 = Room.objects.create(number='415', floor=4, building='Главный корпус')

            # Создаем сотрудников
            self.stdout.write('Создание сотрудников...')
            
            # Руководство
            Contact.objects.create(
                division=div_secretariat,
                department=dept_management,
                position=pos_advisor,
                room=room_751,
                full_name='Иванов Иван Иванович',
                work_phone='74-92-35',
                employment_type='full_time',
                display_order=1
            )
            
            Contact.objects.create(
                division=div_secretariat,
                department=dept_management,
                position=pos_press_secretary,
                room=room_750,
                full_name='Петрова Мария Сергеевна',
                work_phone='74-03-18',
                employment_type='full_time',
                display_order=2
            )
            
            Contact.objects.create(
                division=None,
                department=dept_management,
                position=pos_advisor,
                room=room_755,
                full_name='Сидоров Петр Александрович',
                work_phone='74-12-00',
                employment_type='full_time',
                display_order=1
            )
            
            # Внештатный советник
            Contact.objects.create(
                division=None,
                department=dept_management,
                position=pos_external_advisor,
                room=room_740,
                full_name='Кузнецова Анна Владимировна',
                work_phone='74-13-72',
                employment_type='external',
                display_order=5
            )
            
            # Департамент внутреннего аудита
            Contact.objects.create(
                division=div_audit,
                department=dept_audit,
                position=pos_head,
                room=room_201,
                full_name='Смирнов Алексей Николаевич',
                work_phone='74-20-10',
                employment_type='full_time',
                display_order=1
            )
            
            Contact.objects.create(
                division=div_audit,
                department=dept_audit,
                position=pos_specialist,
                room=room_201,
                full_name='Козлова Елена Дмитриевна',
                work_phone='74-20-11',
                employment_type='full_time',
                display_order=2
            )
            
            # Департамент анализа и стратегического планирования
            Contact.objects.create(
                division=div_strategy,
                department=dept_planning,
                position=pos_head,
                room=room_302,
                full_name='Новиков Дмитрий Васильевич',
                work_phone='74-30-20',
                employment_type='full_time',
                display_order=1
            )
            
            Contact.objects.create(
                division=div_strategy,
                department=dept_planning,
                position=pos_lead_specialist,
                room=room_302,
                full_name='Морозова Ольга Игоревна',
                work_phone='74-30-21',
                employment_type='full_time',
                display_order=2
            )
            
            Contact.objects.create(
                division=div_analysis,
                department=dept_planning,
                position=pos_head,
                room=room_302,
                full_name='Лебедев Сергей Павлович',
                work_phone='74-30-30',
                employment_type='full_time',
                display_order=1
            )
            
            # Департамент экономики и финансов
            Contact.objects.create(
                division=div_budget_planning,
                department=dept_economics,
                position=pos_head,
                room=room_415,
                full_name='Волков Андрей Михайлович',
                work_phone='74-41-10',
                employment_type='full_time',
                display_order=1
            )
            
            Contact.objects.create(
                division=div_budget_planning,
                department=dept_economics,
                position=pos_specialist,
                room=room_415,
                full_name='Зайцева Татьяна Анатольевна',
                work_phone='74-41-11',
                employment_type='full_time',
                display_order=2
            )
            
            Contact.objects.create(
                division=div_accounting,
                department=dept_economics,
                position=pos_head,
                room=room_415,
                full_name='Соколов Виктор Сергеевич',
                work_phone='74-41-20',
                employment_type='full_time',
                display_order=1
            )
            
            # Юридический департамент
            Contact.objects.create(
                division=div_legal_expertise,
                department=dept_law,
                position=pos_head,
                room=room_415,
                full_name='Павлов Игорь Владимирович',
                work_phone='74-41-30',
                employment_type='full_time',
                display_order=1
            )
            
            Contact.objects.create(
                division=div_legal_support,
                department=dept_law,
                position=pos_head,
                room=room_415,
                full_name='Семенова Наталья Борисовна',
                work_phone='74-41-40',
                employment_type='full_time',
                display_order=1
            )
            
            # Совместитель
            Contact.objects.create(
                division=div_legal_support,
                department=dept_law,
                position=pos_lead_specialist,
                room=room_415,
                full_name='Федоров Роман Игоревич',
                work_phone='74-41-41',
                mobile_phone='+7 777 123 4567',
                employment_type='part_time',
                display_order=2
            )

        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*50}\n'
            f'Тестовые данные успешно созданы!\n'
            f'{"="*50}\n'
            f'Создано:\n'
            f'  - Департаментов: {Department.objects.count()}\n'
            f'  - Отделов: {Division.objects.count()}\n'
            f'  - Должностей: {Position.objects.count()}\n'
            f'  - Кабинетов: {Room.objects.count()}\n'
            f'  - Сотрудников: {Contact.objects.count()}\n'
            f'{"="*50}'
        ))
