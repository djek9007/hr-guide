from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, F
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .models import Contact, Department, Division, Position, Room, Vacancy


# Кастомный LogoutView: разрешаем GET для /logout/ (переход по адресу, закладка, «Обновить» на странице ошибки).
# Django 5.x по умолчанию принимает только POST; GET делегируем в post().
class LogoutViewGetAllowed(auth_views.LogoutView):
    http_method_names = ['get', 'head', 'post', 'options']

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


def list_contacts(request):
    """
    Представление для отображения списка всех сотрудников с иерархией.
    Показывает структуру: Департаменты/Комитеты -> Управления -> Сотрудники.
    Сортировка: сначала по display_order (если указан), потом по названию/ФИО.
    Оптимизация: Используем 3 запроса вместо N+1.
    """
    from collections import defaultdict
    
    # 1. Загружаем все департаменты
    departments = list(Department.objects.order_by(
        F('display_order').asc(nulls_last=True), 'type', 'name_ru'
    ))

    # 2. Загружаем все управления
    all_divisions = Division.objects.select_related('department').order_by(
        F('display_order').asc(nulls_last=True), 'name_ru'
    )
    
    # Группируем управления по департаментам
    divisions_by_dept = defaultdict(list)
    for div in all_divisions:
        if div.department_id:
            divisions_by_dept[div.department_id].append(div)

    # 3. Загружаем всех сотрудников, которые привязаны к департаменту или управлению
    # Остальные (сироты) загружаются отдельным запросом для пагинации ниже
    hierarchy_contacts = Contact.objects.filter(
        Q(department__isnull=False) | Q(division__isnull=False)
    ).select_related('room', 'position', 'department', 'division').order_by(
        'employment_type',
        F('display_order').asc(nulls_last=True),
        'full_name'
    )
    
    # Группируем сотрудников
    contacts_by_dept_direct = defaultdict(list) # Те, кто прямо в департаменте (без управления)
    contacts_by_division = defaultdict(list)    # Те, кто в управлении (независимо от department_id)

    for contact in hierarchy_contacts:
        if contact.division_id:
            # Если есть управление, кладем в папку управления
            # (даже если department_id тоже заполнен, приоритет у управления)
            contacts_by_division[contact.division_id].append(contact)
        elif contact.department_id:
            # Если управления нет, но есть департамент - кладем в департамент
            contacts_by_dept_direct[contact.department_id].append(contact)

    # 4. Собираем структуру
    for department in departments:
        # Получаем управления этого департамента
        dept_divisions = divisions_by_dept.get(department.id, [])
        
        divisions_with_contacts = []
        # Обрабатываем управления
        for division in dept_divisions:
            # Берем сотрудников этого управления
            division_contacts = contacts_by_division.get(division.id, [])
            division.contacts_sorted = division_contacts
            
            # Добавляем управление в список, только если в нем есть сотрудники
            if division_contacts:
                divisions_with_contacts.append(division)
        
        department.divisions_list = divisions_with_contacts
        
        # Берем сотрудников, привязанных напрямую к департаменту
        department.contacts_sorted = contacts_by_dept_direct.get(department.id, [])
        
        # Считаем общее количество
        total_contacts_in_dept = len(department.contacts_sorted)
        for division in department.divisions_list:
            total_contacts_in_dept += len(division.contacts_sorted)
        department.total_contacts_count = total_contacts_in_dept

    # 4.5. Обрабатываем независимые управления (без департамента)
    # Они должны отображаться как департаменты (на верхнем уровне)
    independent_divisions = [div for div in all_divisions if not div.department_id]
    
    for division in independent_divisions:
        # Берем сотрудников этого управления
        division_contacts = contacts_by_division.get(division.id, [])
        division.contacts_sorted = division_contacts
        
        # Эмулируем структуру департамента
        division.divisions_list = []
        division.total_contacts_count = len(division_contacts)
        
        # Помечаем как независимое управление, чтобы корректно обработать в шаблоне
        division.is_independent_division = True
        
        # Добавляем в общий список
        departments.append(division)
        
    # Пересортируем общий список, чтобы учесть добавленные управления
    def get_sort_key(obj):
        order = getattr(obj, 'display_order', None)
        if order is None:
            order = float('inf')
        name = getattr(obj, 'name_ru', '')
        return (order, name)
        
    departments.sort(key=get_sort_key)

    # 5. Получаем сотрудников без управления и без департамента (как и раньше)
    contacts_without_department = Contact.objects.filter(
        department__isnull=True,
        division__isnull=True
    ).select_related('room', 'position').order_by(
        F('display_order').asc(nulls_last=True),
        'full_name'
    )

    # Пагинация для сотрудников без управления
    paginator = Paginator(contacts_without_department, 20)
    page = request.GET.get('page', 1)

    try:
        contacts_page = paginator.page(page)
    except PageNotAnInteger:
        contacts_page = paginator.page(1)
    except EmptyPage:
        contacts_page = paginator.page(paginator.num_pages)

    # Подсчитываем общее количество управлений
    total_divisions = Division.objects.count()

    context = {
        'departments': departments,
        'contacts_without_department': contacts_page,
        'paginator': paginator,
        'total_contacts': Contact.objects.count(),
        'total_divisions': total_divisions,
    }

    return render(request, 'contacts/list.html', context)


def search_contacts(request):
    """
    Представление для поиска сотрудников с использованием фильтров.
    Поддерживает фильтрацию по: номеру кабинета, ФИО, должности, управлению, телефону, типу трудоустройства.
    Доступно всем пользователям (публичный доступ).
    """
    # Получаем параметры фильтров
    room_number = request.GET.get('room', '').strip()
    full_name = request.GET.get('name', '').strip()
    position_id = request.GET.get('position', '').strip()
    division_id = request.GET.get('division', '').strip()
    department_id = request.GET.get('department', '').strip()
    phone = request.GET.get('phone', '').strip()
    employment_type = request.GET.get('employment_type', '').strip()

    # Базовый queryset с оптимизацией запросов (division — для вывода управления или департамента/комитета при его отсутствии)
    contacts = Contact.objects.select_related('room', 'position', 'department', 'division').all()

    # Применяем фильтры
    filters = Q()

    # Фильтр по номеру кабинета (приоритетный)
    if room_number:
        filters &= Q(room__number__icontains=room_number)

    # Фильтр по ФИО
    if full_name:
        filters &= Q(full_name__icontains=full_name)

    # Фильтр по должности
    if position_id:
        try:
            filters &= Q(position_id=int(position_id))
        except ValueError:
            pass

    # Фильтр по управлению
    if division_id:
        try:
            filters &= Q(division_id=int(division_id))
        except ValueError:
            pass
    
    # Фильтр по департаменту
    # Если выбран департамент - показываем сотрудников всех управлений внутри него + сотрудников департамента
    if department_id:
        try:
            dept_id = int(department_id)
            department = Department.objects.filter(id=dept_id).first()
            if department:
                # Получаем ID всех управлений внутри департамента
                division_ids = list(department.divisions.values_list('id', flat=True))
                # Фильтруем: сотрудники управлений + сотрудники напрямую в департаменте
                filters &= (Q(division_id__in=division_ids) | Q(department_id=dept_id))
        except ValueError:
            pass

    # Фильтр по телефону (рабочий или мобильный)
    if phone:
        filters &= (Q(work_phone__icontains=phone) | Q(mobile_phone__icontains=phone))
    
    # Фильтр по типу трудоустройства
    if employment_type:
        filters &= Q(employment_type=employment_type)

    # Применяем все фильтры
    if filters:
        contacts = contacts.filter(filters)
    # Если нет фильтров, показываем все записи (с пагинацией в будущем)

    # Сортируем результаты: сначала по display_order (nulls_last), потом по номеру кабинета, потом по ФИО
    contacts = contacts.order_by(
        F('display_order').asc(nulls_last=True),
        'room__number',
        'full_name'
    )

    # Пагинация - 20 записей на страницу
    paginator = Paginator(contacts, 20)
    page = request.GET.get('page', 1)

    try:
        contacts_page = paginator.page(page)
    except PageNotAnInteger:
        contacts_page = paginator.page(1)
    except EmptyPage:
        contacts_page = paginator.page(paginator.num_pages)

    # Получаем списки для выпадающих меню
    departments = Department.objects.all().order_by(
        'type', F('display_order').asc(nulls_last=True), 'name_ru'
    )
    divisions = Division.objects.select_related('department').order_by(
        F('display_order').asc(nulls_last=True), 'name_ru'
    )
    positions = Position.objects.all().order_by('name_ru')

    # Проверяем, есть ли активные фильтры
    has_active_filters = any([room_number, full_name, position_id, division_id, department_id, phone, employment_type])

    context = {
        'contacts': contacts_page,
        'paginator': paginator,
        'total_results': contacts.count(),
        'departments': departments,
        'divisions': divisions,
        'positions': positions,
        # Значения фильтров для формы
        'room_number': room_number,
        'full_name': full_name,
        'position_id': position_id,
        'division_id': division_id,
        'department_id': department_id,
        'phone': phone,
        'employment_type': employment_type,
        'has_active_filters': has_active_filters,
    }

    # Если это HTMX запрос, возвращаем только результаты
    if request.headers.get('HX-Request'):
        return render(request, 'contacts/partials/search_results.html', context)

    # Обычный запрос - возвращаем полную страницу
    return render(request, 'contacts/search.html', context)


def list_vacancies(request):
    """
    Представление для отображения списка вакансий.
    Показывает только активные вакансии.
    """
    vacancies = Vacancy.objects.select_related('department').filter(
        is_active=True
    ).order_by(
        F('display_order').asc(nulls_last=True),
        '-created_at'
    )

    paginator = Paginator(vacancies, 10)
    page = request.GET.get('page', 1)

    try:
        vacancies_page = paginator.page(page)
    except PageNotAnInteger:
        vacancies_page = paginator.page(1)
    except EmptyPage:
        vacancies_page = paginator.page(paginator.num_pages)

    context = {
        'vacancies': vacancies_page,
        'paginator': paginator,
        'total_vacancies': vacancies.count(),
    }

    return render(request, 'contacts/vacancies.html', context)


def vacancy_detail(request, pk):
    """
    Представление для детального просмотра вакансии.
    """
    vacancy = get_object_or_404(
        Vacancy.objects.select_related('department'),
        pk=pk,
        is_active=True
    )

    context = {
        'vacancy': vacancy,
    }

    return render(request, 'contacts/vacancy_detail.html', context)


@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Представление для входа в систему.
    """
    if request.user.is_authenticated:
        return redirect('messaging:chat')

    if request.method == 'POST':
        # Поле может содержать username или email
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if username_or_email and password:
            # Аутентифицируем по username или email
            user = authenticate(request, username=username_or_email, password=password)
            if user is not None:
                login(request, user)
                
                # Проверяем, используется ли стандартный пароль Chat2026
                if user.check_password('Chat2026'):
                    # Если пароль стандартный, перенаправляем на смену пароля
                    messages.warning(request, _('Для безопасности необходимо сменить стандартный пароль.'))
                    return redirect('contacts:change_password')
                
                messages.success(request, _('Вы успешно вошли в систему.'))
                next_url = request.GET.get('next', None)
                if next_url:
                    return redirect(next_url)
                return redirect('messaging:chat')
            else:
                messages.error(request, _('Неверное имя пользователя, email или пароль.'))
        else:
            messages.error(request, _('Пожалуйста, заполните все поля.'))

    return render(request, 'accounts/login.html')


@login_required
@require_http_methods(["GET", "POST"])
def change_password_view(request):
    """
    Представление для смены пароля.
    Обязательно для пользователей со стандартным паролем Chat2026.
    """
    if request.method == 'POST':
        old_password = request.POST.get('old_password', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
        # Проверяем текущий пароль
        if not request.user.check_password(old_password):
            messages.error(request, _('Неверный текущий пароль.'))
            return render(request, 'accounts/change_password.html')
        
        # Проверяем, что новый пароль не совпадает со стандартным
        if new_password == 'Chat2026':
            messages.error(request, _('Новый пароль не может совпадать со стандартным паролем.'))
            return render(request, 'accounts/change_password.html')
        
        # Проверяем совпадение нового пароля и подтверждения
        if new_password != confirm_password:
            messages.error(request, _('Новые пароли не совпадают.'))
            return render(request, 'accounts/change_password.html')
        
        # Проверяем минимальную длину пароля
        if len(new_password) < 8:
            messages.error(request, _('Пароль должен содержать минимум 8 символов.'))
            return render(request, 'accounts/change_password.html')
        
        # Устанавливаем новый пароль
        request.user.set_password(new_password)
        request.user.save()
        
        messages.success(request, _('Пароль успешно изменен. Пожалуйста, войдите снова с новым паролем.'))
        from django.contrib.auth import logout
        logout(request)
        return redirect('login')
    
    return render(request, 'accounts/change_password.html')


def developer_contact(request):
    """
    Страница «Связь с разработчиком»: контакты (email, Telegram) из настроек.
    Контекст developer_* передаётся через context_processors.
    Доступна всем пользователям без авторизации.
    """
    return render(request, 'contacts/developer_contact.html')


def chat_view(request):
    """
    Представление для страницы чата.
    Пока что простая заглушка, позже будет реализован полноценный функционал.
    """
    context = {}
    return render(request, 'contacts/chat.html', context)