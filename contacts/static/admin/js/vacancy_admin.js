/**
 * Динамическая фильтрация управлений по выбранному департаменту в админке вакансий.
 * При изменении департамента обновляется список доступных управлений.
 * 
 * Логика работы:
 * - Если департамент выбран - показываются управления этого департамента
 * - Если департамент не выбран - показываются независимые управления (без департамента)
 * - Учитывается, что у департамента может не быть управлений, а управление может быть без департамента
 */
(function($) {
    'use strict';

    $(document).ready(function() {
        // Находим поля департамента и управления
        var $departmentField = $('#id_department');
        var $divisionField = $('#id_division');

        // Функция для обновления списка управлений
        function updateDivisions() {
            var departmentId = $departmentField.val();
            
            // Сохраняем текущее значение управления
            var currentDivisionId = $divisionField.val();
            
            // Всегда загружаем управления через AJAX (для выбранного департамента или независимые)
            $.ajax({
                url: '/admin/contacts/vacancy/get-divisions-by-department/',
                data: {
                    'department_id': departmentId || ''  // Отправляем пустую строку, если департамент не выбран
                },
                dataType: 'json',
                success: function(data) {
                    // Очищаем текущие опции
                    $divisionField.empty();
                    
                    // Добавляем пустую опцию
                    $divisionField.append($('<option></option>').attr('value', '').text('---------'));
                    
                    // Добавляем управления (для выбранного департамента или независимые)
                    $.each(data.divisions, function(index, division) {
                        var $option = $('<option></option>')
                            .attr('value', division.id)
                            .text(division.name_ru);
                        
                        // Если это было ранее выбранное управление, выбираем его
                        if (currentDivisionId == division.id) {
                            $option.attr('selected', 'selected');
                        }
                        
                        $divisionField.append($option);
                    });
                },
                error: function() {
                    // В случае ошибки просто очищаем поле
                    $divisionField.empty();
                    $divisionField.append($('<option></option>').attr('value', '').text('---------'));
                }
            });
        }

        // Обработчик изменения департамента
        $departmentField.on('change', updateDivisions);
        
        // При загрузке страницы всегда обновляем управления
        // (показываем либо управления выбранного департамента, либо независимые)
        updateDivisions();
    });
})(django.jQuery);
