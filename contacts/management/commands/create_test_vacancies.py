"""
Команда Django для создания тестовых вакансий.
Использование: python manage.py create_test_vacancies
"""
from django.core.management.base import BaseCommand
from contacts.models import Vacancy, Department, Position


class Command(BaseCommand):
    help = 'Создает 10 тестовых вакансий в базе данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Количество вакансий для создания (по умолчанию: 10)',
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Получаем первый доступный отдел, если есть
        department = Department.objects.first()
        
        # Список тестовых вакансий с должностями
        vacancies_data = [
            {
                'position_name_ru': 'Специалист по работе с документацией',
                'position_name_kk': 'Құжаттамамен жұмыс істеу маманы',
                'description_ru': '<p>Требуется специалист для работы с внутренней документацией министерства. Обязанности включают систематизацию документов, ведение архива и подготовку отчетов.</p>',
                'description_kk': '<p>Министрліктің ішкі құжаттамасымен жұмыс істеу үшін маман қажет. Міндеттер: құжаттарды жүйелеу, мұрағатты басқару және есептер дайындау.</p>',
                'requirements_and_conditions_ru': '<p><strong>Требования:</strong></p><ul><li>Высшее образование</li><li>Опыт работы с документацией от 2 лет</li><li>Знание делопроизводства</li><li>Внимательность и аккуратность</li></ul><p><strong>Условия работы:</strong></p><ul><li>Официальное трудоустройство</li><li>График работы: 5/2</li><li>Социальный пакет</li></ul>',
                'requirements_and_conditions_kk': '<p><strong>Талаптар:</strong></p><ul><li>Жоғары білім</li><li>Құжаттамамен жұмыс тәжірибесі 2 жылдан</li><li>Құжат айналымын білу</li></ul>',
                'contact_info': 'hr@mki.gov.kz, +7 (7172) 111-111',
            },
            {
                'position_name_ru': 'Экономист-аналитик',
                'position_name_kk': 'Экономист-сарапшы',
                'description_ru': '<p>Вакансия для экономиста-аналитика. Работа с финансовыми отчетами, анализ бюджетных показателей, подготовка экономических обзоров.</p>',
                'description_kk': '<p>Экономист-сарапшыға вакансия. Қаржылық есептермен жұмыс, бюджет көрсеткіштерін талдау, экономикалық шолулар дайындау.</p>',
                'requirements_and_conditions_ru': '<p><strong>Требования:</strong></p><ul><li>Высшее экономическое образование</li><li>Опыт работы в бюджетной сфере</li><li>Знание Excel, 1С</li></ul><p><strong>Условия:</strong> Полный рабочий день, стабильная зарплата</p>',
                'requirements_and_conditions_kk': '<p><strong>Талаптар:</strong></p><ul><li>Жоғары экономикалық білім</li><li>Бюджет саласындағы тәжірибе</li></ul>',
                'contact_info': 'economy@mki.gov.kz, +7 (7172) 222-222',
            },
            {
                'position_name_ru': 'IT-специалист',
                'position_name_kk': 'IT-маман',
                'description_ru': '<p>Требуется IT-специалист для поддержки информационных систем министерства. Администрирование серверов, техническая поддержка пользователей.</p>',
                'description_kk': '<p>Министрліктің ақпараттық жүйелерін қолдау үшін IT-маман қажет. Серверлерді басқару, пайдаланушыларға техникалық көмек көрсету.</p>',
                'requirements_and_conditions_ru': '<p><strong>Требования:</strong></p><ul><li>Высшее техническое образование</li><li>Знание Linux/Windows серверов</li><li>Опыт работы с базами данных</li></ul>',
                'requirements_and_conditions_kk': '<p><strong>Талаптар:</strong></p><ul><li>Жоғары техникалық білім</li><li>Linux/Windows серверлерін білу</li></ul>',
                'contact_info': 'it@mki.gov.kz, +7 (7172) 333-333',
            },
            {
                'position_name_ru': 'Переводчик',
                'position_name_kk': 'Аудармашы',
                'description_ru': '<p>Вакансия переводчика казахского и русского языков. Перевод официальных документов, участие в международных мероприятиях.</p>',
                'description_kk': '<p>Қазақ және орыс тілдерін аудармашы вакансиясы. Ресми құжаттарды аудару, халықаралық іс-шараларға қатысу.</p>',
                'requirements_and_conditions_ru': '<p><strong>Требования:</strong></p><ul><li>Высшее лингвистическое образование</li><li>Свободное владение казахским и русским языками</li><li>Знание английского языка приветствуется</li></ul>',
                'requirements_and_conditions_kk': '<p><strong>Талаптар:</strong></p><ul><li>Жоғары тіл білімі</li><li>Қазақ және орыс тілдерін еркін меңгеру</li></ul>',
                'contact_info': 'translation@mki.gov.kz, +7 (7172) 444-444',
            },
            {
                'position_name_ru': 'Юрист',
                'position_name_kk': 'Заңгер',
                'description_ru': '<p>Требуется юрист для работы с нормативно-правовой базой. Подготовка правовых заключений, работа с договорами.</p>',
                'description_kk': '<p>Құқықтық-нормативтік базамен жұмыс істеу үшін заңгер қажет. Құқықтық қорытындылар дайындау, келісім-шарттармен жұмыс.</p>',
                'requirements_and_conditions_ru': '<p><strong>Требования:</strong></p><ul><li>Высшее юридическое образование</li><li>Опыт работы в государственных органах</li><li>Знание административного права</li></ul>',
                'requirements_and_conditions_kk': '<p><strong>Талаптар:</strong></p><ul><li>Жоғары заң білімі</li><li>Мемлекеттік органдардағы тәжірибе</li></ul>',
                'contact_info': 'legal@mki.gov.kz, +7 (7172) 555-555',
            },
            {
                'position_name_ru': 'Специалист по связям с общественностью',
                'position_name_kk': 'Қоғаммен байланыс маманы',
                'description_ru': '<p>Вакансия специалиста по PR. Работа со СМИ, организация пресс-конференций, ведение социальных сетей министерства.</p>',
                'description_kk': '<p>PR маманы вакансиясы. БАҚ-пен жұмыс, баспасөз конференцияларын ұйымдастыру, министрліктің әлеуметтік желілерін басқару.</p>',
                'requirements_and_conditions_ru': '<p><strong>Требования:</strong></p><ul><li>Высшее образование в области журналистики или PR</li><li>Опыт работы со СМИ</li><li>Навыки работы с социальными сетями</li></ul>',
                'requirements_and_conditions_kk': '<p><strong>Талаптар:</strong></p><ul><li>Журналистика немесе PR саласында жоғары білім</li><li>БАҚ-пен жұмыс тәжірибесі</li></ul>',
                'contact_info': 'pr@mki.gov.kz, +7 (7172) 666-666',
            },
            {
                'position_name_ru': 'Бухгалтер',
                'position_name_kk': 'Бухгалтер',
                'description_ru': '<p>Требуется бухгалтер для ведения финансового учета. Работа с первичной документацией, начисление зарплаты, составление отчетности.</p>',
                'description_kk': '<p>Қаржылық есепті басқару үшін бухгалтер қажет. Бастапқы құжаттамамен жұмыс, жалақы есептеу, есептілік дайындау.</p>',
                'requirements_and_conditions_ru': '<p><strong>Требования:</strong></p><ul><li>Высшее экономическое или бухгалтерское образование</li><li>Опыт работы от 3 лет</li><li>Знание 1С:Бухгалтерия</li></ul>',
                'requirements_and_conditions_kk': '<p><strong>Талаптар:</strong></p><ul><li>Жоғары экономикалық немесе бухгалтерлік білім</li><li>3 жылдан тәжірибе</li></ul>',
                'contact_info': 'accounting@mki.gov.kz, +7 (7172) 777-777',
            },
            {
                'position_name_ru': 'Секретарь-референт',
                'position_name_kk': 'Хатшы-референт',
                'description_ru': '<p>Вакансия секретаря-референта. Организация рабочего дня руководителя, работа с документами, прием звонков.</p>',
                'description_kk': '<p>Хатшы-референт вакансиясы. Басшының жұмыс күнін ұйымдастыру, құжаттармен жұмыс, телефон қоңырауларын қабылдау.</p>',
                'requirements_and_conditions_ru': '<p><strong>Требования:</strong></p><ul><li>Высшее образование</li><li>Знание делопроизводства</li><li>Грамотная речь, знание языков</li></ul>',
                'requirements_and_conditions_kk': '<p><strong>Талаптар:</strong></p><ul><li>Жоғары білім</li><li>Құжат айналымын білу</li></ul>',
                'contact_info': 'secretary@mki.gov.kz, +7 (7172) 888-888',
            },
            {
                'position_name_ru': 'Менеджер проектов',
                'position_name_kk': 'Жоба менеджері',
                'description_ru': '<p>Требуется менеджер проектов для координации культурных и информационных проектов министерства.</p>',
                'description_kk': '<p>Министрліктің мәдени және ақпараттық жобаларын үйлестіру үшін жоба менеджері қажет.</p>',
                'requirements_and_conditions_ru': '<p><strong>Требования:</strong></p><ul><li>Высшее образование</li><li>Опыт управления проектами</li><li>Навыки планирования и контроля</li></ul>',
                'requirements_and_conditions_kk': '<p><strong>Талаптар:</strong></p><ul><li>Жоғары білім</li><li>Жобаларды басқару тәжірибесі</li></ul>',
                'contact_info': 'projects@mki.gov.kz, +7 (7172) 999-999',
            },
            {
                'position_name_ru': 'Архивариус',
                'position_name_kk': 'Мұрағатшы',
                'description_ru': '<p>Вакансия архивариуса. Ведение архивного фонда, систематизация документов, обеспечение сохранности архивных материалов.</p>',
                'description_kk': '<p>Мұрағатшы вакансиясы. Мұрағат қорын басқару, құжаттарды жүйелеу, мұрағат материалдарының сақталуын қамтамасыз ету.</p>',
                'requirements_and_conditions_ru': '<p><strong>Требования:</strong></p><ul><li>Высшее образование</li><li>Знание архивного дела</li><li>Внимательность, аккуратность</li></ul>',
                'requirements_and_conditions_kk': '<p><strong>Талаптар:</strong></p><ul><li>Жоғары білім</li><li>Мұрағат ісін білу</li></ul>',
                'contact_info': 'archive@mki.gov.kz, +7 (7172) 000-000',
            },
        ]
        
        created_count = 0
        
        for i, vacancy_data in enumerate(vacancies_data[:count]):
            # Создаем или получаем должность
            position, created = Position.objects.get_or_create(
                name_ru=vacancy_data['position_name_ru'],
                defaults={
                    'name_kk': vacancy_data.get('position_name_kk', ''),
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Создана должность: {position.name_ru}')
                )
            
            # Создаем вакансию
            vacancy = Vacancy.objects.create(
                position=position,
                department=department,
                description_ru=vacancy_data.get('description_ru', ''),
                description_kk=vacancy_data.get('description_kk', ''),
                requirements_and_conditions_ru=vacancy_data.get('requirements_and_conditions_ru', ''),
                requirements_and_conditions_kk=vacancy_data.get('requirements_and_conditions_kk', ''),
                contact_info=vacancy_data.get('contact_info', ''),
                is_active=True,
                display_order=i + 1,
            )
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Создана вакансия: {vacancy.get_title()}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nУспешно создано {created_count} тестовых вакансий!')
        )
