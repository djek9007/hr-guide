from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, F
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .models import Contact, Department, Division, Position, Room, Vacancy


def list_contacts(request):
    """
    Представление для отображения списка всех сотрудников с иерархией.
    Показывает структуру: Департаменты -> Управления -> Сотрудники.
    Сортировка: сначала по display_order (если указан), потом по названию/ФИО.
    """
    # Получаем все департаменты с их управлениями и сотрудниками
    departments = Department.objects.prefetch_related(
        'contacts__room',
        'contacts__position',
        'divisions__contacts__room',
        'divisions__contacts__position'
    ).order_by(F('display_order').asc(nulls_last=True), 'type', 'name_ru')

    # Для каждого департамента получаем его управления и контакты
    for department in departments:
        # Получаем управления внутри департамента (используем другое имя для присвоения)
        divisions_queryset = department.divisions.all().prefetch_related(
            'contacts__room', 
            'contacts__position'
        ).order_by(
            F('display_order').asc(nulls_last=True),
            'name_ru'
        )
        # Присваиваем в список, а не в related manager
        department.divisions_list = list(divisions_queryset)
        
        # Получаем сотрудников напрямую в департаменте (ТОЛЬКО те, у которых НЕТ управления)
        # ВАЖНО: Если у сотрудника есть division, он НЕ должен попадать сюда, даже если у него указан этот department
        department.contacts_sorted = list(
            department.contacts.filter(
                division__isnull=True  # Только сотрудники без управления
            ).select_related('room', 'position').order_by(
                'employment_type',
                F('display_order').asc(nulls_last=True),
                'full_name'
            )
        )
        
        # Для каждого управления внутри департамента сортируем сотрудников
        # Фильтруем только управления, где есть сотрудники
        # ВАЖНО: Сотрудник с division всегда показывается только в управлении, даже если у него есть department
        divisions_with_contacts = []
        for division in department.divisions_list:
            # Просто получаем всех сотрудников управления - если у них есть division, они должны показываться только здесь
            division_contacts = division.contacts.all().select_related('room', 'position').order_by(
                'employment_type',
                F('display_order').asc(nulls_last=True),
                'full_name'
            )
            division.contacts_sorted = list(division_contacts)
            # Добавляем только управления с сотрудниками
            if division.contacts_sorted:
                divisions_with_contacts.append(division)
        
        # Заменяем список на отфильтрованный
        department.divisions_list = divisions_with_contacts
        
        # Пересчитываем общее количество сотрудников в департаменте
        # (сотрудники напрямую в департаменте + сотрудники во всех управлениях)
        total_contacts_in_dept = len(department.contacts_sorted)
        for division in department.divisions_list:
            total_contacts_in_dept += len(division.contacts_sorted)
        department.total_contacts_count = total_contacts_in_dept

    # Получаем сотрудников без управления и без департамента с сортировкой
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

    # Базовый queryset с оптимизацией запросов
    contacts = Contact.objects.select_related('room', 'position', 'department').all()

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
        return redirect('contacts:search')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, _('Вы успешно вошли в систему.'))
                next_url = request.GET.get('next', None)
                if next_url:
                    return redirect(next_url)
                return redirect('contacts:search')
            else:
                messages.error(request, _('Неверное имя пользователя или пароль.'))
        else:
            messages.error(request, _('Пожалуйста, заполните все поля.'))

    return render(request, 'accounts/login.html')


def chat_view(request):
    """
    Представление для страницы чата.
    Пока что простая заглушка, позже будет реализован полноценный функционал.
    """
    context = {}
    return render(request, 'contacts/chat.html', context)