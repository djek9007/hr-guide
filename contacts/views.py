from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, F
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .models import Contact, Department, Position, Room, Vacancy


def list_contacts(request):
    """
    Представление для отображения списка всех контактов с иерархией отделов.
    Показывает структуру отделов и сотрудников по отделам.
    Сортировка: сначала по display_order (если указан), потом по ФИО.
    """
    # Получаем все отделы с их контактами
    # Сначала по display_order (nulls_last), потом по названию
    departments = Department.objects.prefetch_related(
        'contacts__room',
        'contacts__position',
        'contacts__department'
    ).all().order_by(F('display_order').asc(nulls_last=True), 'name_ru')

    # Применяем сортировку к контактам в каждом отделе
    # Сначала по display_order (nulls_last), потом по ФИО
    for department in departments:
        department.contacts_sorted = department.contacts.all().select_related('room', 'position').order_by(
            F('display_order').asc(nulls_last=True),
            'full_name'
        )

    # Получаем контакты без отдела с сортировкой
    contacts_without_department = Contact.objects.filter(
        department__isnull=True
    ).select_related('room', 'position').order_by(
        F('display_order').asc(nulls_last=True),
        'full_name'
    )

    # Пагинация для контактов без отдела
    paginator = Paginator(contacts_without_department, 20)
    page = request.GET.get('page', 1)

    try:
        contacts_page = paginator.page(page)
    except PageNotAnInteger:
        contacts_page = paginator.page(1)
    except EmptyPage:
        contacts_page = paginator.page(paginator.num_pages)

    context = {
        'departments': departments,
        'contacts_without_department': contacts_page,
        'paginator': paginator,
        'total_contacts': Contact.objects.count(),
    }

    return render(request, 'contacts/list.html', context)


def search_contacts(request):
    """
    Представление для поиска контактов с использованием фильтров.
    Поддерживает фильтрацию по: номеру кабинета, ФИО, должности, отделу, телефону.
    Доступно всем пользователям (публичный доступ).
    """
    # Получаем параметры фильтров
    room_number = request.GET.get('room', '').strip()
    full_name = request.GET.get('name', '').strip()
    position_id = request.GET.get('position', '').strip()
    department_id = request.GET.get('department', '').strip()
    phone = request.GET.get('phone', '').strip()

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

    # Фильтр по отделу
    if department_id:
        try:
            filters &= Q(department_id=int(department_id))
        except ValueError:
            pass

    # Фильтр по телефону (рабочий или мобильный)
    if phone:
        filters &= (Q(work_phone__icontains=phone) | Q(mobile_phone__icontains=phone))

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
    departments = Department.objects.all().order_by('name_ru')
    positions = Position.objects.all().order_by('name_ru')

    # Проверяем, есть ли активные фильтры
    has_active_filters = any([room_number, full_name, position_id, department_id, phone])

    context = {
        'contacts': contacts_page,
        'paginator': paginator,
        'total_results': contacts.count(),
        'departments': departments,
        'positions': positions,
        # Значения фильтров для формы
        'room_number': room_number,
        'full_name': full_name,
        'position_id': position_id,
        'department_id': department_id,
        'phone': phone,
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
