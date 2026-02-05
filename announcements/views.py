from django.views.generic import ListView, DetailView
from .models import Announcement


class AnnouncementListView(ListView):
    """
    Публичное представление для отображения списка объявлений с пагинацией.
    
    Доступно без авторизации. Отображает все объявления, отсортированные
    по дате создания (новые первыми), с пагинацией по 20 записей на страницу.
    
    Requirements: 4.1, 4.3, 4.4, 4.5
    """
    model = Announcement
    template_name = 'announcements/list.html'
    context_object_name = 'announcements'
    paginate_by = 20
    
    def get_queryset(self):
        """
        Возвращает queryset объявлений, отсортированных по дате публикации (DESC).
        
        Returns:
            QuerySet: Все объявления, отсортированные по published_date в порядке убывания
        """
        return Announcement.objects.all().order_by('-published_date')
    
    def get_context_data(self, **kwargs):
        """
        Добавляет текущий язык в контекст шаблона.
        
        Returns:
            dict: Контекст с добавленным текущим языком интерфейса
        """
        context = super().get_context_data(**kwargs)
        context['current_language'] = self.request.LANGUAGE_CODE
        return context


class AnnouncementDetailView(DetailView):
    """
    Публичное представление для отображения детальной информации об объявлении.
    
    Доступно без авторизации. Отображает полную информацию об объявлении,
    включая заголовок, содержимое с HTML-форматированием и дату публикации.
    
    Requirements: 4.2
    """
    model = Announcement
    template_name = 'announcements/detail.html'
    context_object_name = 'announcement'
    
    def get_context_data(self, **kwargs):
        """
        Добавляет текущий язык в контекст шаблона.
        
        Returns:
            dict: Контекст с добавленным текущим языком интерфейса
        """
        context = super().get_context_data(**kwargs)
        context['current_language'] = self.request.LANGUAGE_CODE
        return context
