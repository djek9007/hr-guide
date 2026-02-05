# CKEditor Configuration for Announcement System

## Overview

This document describes the CKEditor configuration implemented for the announcement system to ensure secure HTML editing and prevent XSS attacks.

## Configuration Location

The CKEditor configuration is located in `hr_guide/settings.py` under the `CKEDITOR_CONFIGS` setting.

## Security Features

### 1. Removed Dangerous Plugins

The following plugins have been removed to prevent security vulnerabilities:
- `image` - Prevents image upload vulnerabilities
- `flash` - Prevents Flash-based attacks
- `iframe` - Prevents iframe injection
- `forms` - Prevents form injection
- `smiley`, `specialchar`, `pagebreak` - Unnecessary features removed
- `save`, `newpage`, `preview`, `print`, `templates`, `about` - UI features removed

### 2. Removed Dangerous Buttons

The following buttons have been removed:
- `Subscript`, `Superscript` - Prevents potential formatting abuse
- `Anchor` - Prevents anchor-based attacks
- `Styles`, `Format` - Prevents custom style injection

### 3. Allowed HTML Content

Only the following safe HTML elements and attributes are allowed:

#### Safe Tags:
- `<p>` - Paragraphs
- `<br>` - Line breaks
- `<strong>` - Bold text
- `<em>` - Italic text
- `<u>` - Underlined text
- `<s>` - Strikethrough text
- `<ol>`, `<ul>`, `<li>` - Ordered and unordered lists
- `<a>` - Links (with restrictions)

#### Link Restrictions:
Links (`<a>` tags) are allowed with the following restrictions:
- **Allowed attributes**: `href`, `title`
- **Allowed protocols**: `http`, `https`, `mailto`
- **Blocked protocols**: `javascript`, `data`, `file`, etc.

### 4. Disallowed Content

The following dangerous elements are explicitly blocked:
- `<script>` - JavaScript execution
- `*[on*]` - Event handlers (onclick, onload, etc.)
- `<iframe>` - Embedded frames
- `<object>`, `<embed>`, `<applet>` - Embedded objects
- `<form>`, `<input>`, `<button>`, `<select>`, `<textarea>` - Form elements

### 5. Custom Toolbar

A custom toolbar has been configured with only safe formatting options:
- **Row 1**: Bold, Italic, Underline, Strike
- **Row 2**: NumberedList, BulletedList
- **Row 3**: Link, Unlink
- **Row 4**: RemoveFormat
- **Row 5**: Source (for advanced users)

### 6. Paste Protection

- `forcePasteAsPlainText`: False (allows formatted paste but sanitizes)
- `pasteFromWordRemoveFontStyles`: True (removes Word font styles)
- `pasteFromWordRemoveStyles`: True (removes Word styles)

### 7. Additional Settings

- **Language**: Russian (`ru`)
- **Height**: 300px
- **Width**: 100%
- **Auto Paragraph**: True (automatically wraps content in paragraphs)
- **Fill Empty Blocks**: False (prevents empty block creation)

## Requirements Validation

This configuration validates the following requirements:

### Requirement 9.1
✅ **THE Система_Объявлений SHALL использовать django-ckeditor для редактирования содержимого объявлений на обоих языках**

- django-ckeditor 6.7.3 is installed
- Added to INSTALLED_APPS
- RichTextField is used in the Announcement model for both `content_kk` and `content_ru` fields

### Requirement 9.2
✅ **WHEN отображается содержимое объявления, THE Система_Объявлений SHALL безопасно рендерить HTML-форматирование для предотвращения XSS-атак**

- Dangerous plugins removed (script, iframe, forms, etc.)
- Allowed content explicitly defined
- Disallowed content explicitly blocked
- Link protocols restricted to safe protocols only
- Event handlers blocked

### Requirement 9.3
✅ **THE Система_Объявлений SHALL санитизировать предоставленный пользователем HTML для удаления потенциально вредоносных скриптов**

- Client-side sanitization via CKEditor configuration
- Explicit disallowedContent rules
- Paste protection enabled

### Requirement 9.4
✅ **THE Система_Объявлений SHALL сохранять элементы форматирования, такие как жирный шрифт, курсив, списки и ссылки**

- Bold (`<strong>`), Italic (`<em>`), Underline (`<u>`) allowed
- Lists (`<ol>`, `<ul>`, `<li>`) allowed
- Links (`<a>`) allowed with safe protocols

## Testing

Comprehensive tests have been created in `announcements/tests/test_ckeditor_config.py`:

### CKEditorConfigTest (8 tests)
1. ✅ `test_ckeditor_installed_in_apps` - Verifies ckeditor is in INSTALLED_APPS
2. ✅ `test_ckeditor_config_exists` - Verifies CKEDITOR_CONFIGS is defined
3. ✅ `test_ckeditor_config_has_security_settings` - Verifies security settings
4. ✅ `test_safe_html_tags_preserved` - Verifies safe tags are preserved
5. ✅ `test_dangerous_html_sanitized` - Verifies dangerous content handling
6. ✅ `test_link_protocols_restricted` - Verifies link protocol restrictions
7. ✅ `test_ckeditor_toolbar_configured` - Verifies toolbar configuration
8. ✅ `test_ckeditor_language_setting` - Verifies language setting
9. ✅ `test_announcement_model_uses_richtext_field` - Verifies RichTextField usage

### HTMLSanitizationTest (3 tests)
1. ✅ `test_basic_formatting_preserved` - Tests bold, italic, underline
2. ✅ `test_lists_preserved` - Tests ordered and unordered lists
3. ✅ `test_safe_links_preserved` - Tests safe link preservation

**All 12 tests pass successfully.**

## Usage in Admin Interface

When the admin interface is configured (Task 5), CKEditor will automatically be used for the `content_kk` and `content_ru` fields because they are defined as `RichTextField` in the model.

No additional configuration is needed in `admin.py` - the RichTextField automatically renders with the CKEditor widget using the 'default' configuration.

## Static Files

CKEditor static files have been collected:
```bash
docker exec hr-guide-web python manage.py collectstatic --noinput
# Result: 1433 static files copied to '/app/staticfiles'
```

## Security Notes

1. **Client-side sanitization**: CKEditor configuration provides client-side protection
2. **Server-side validation**: Django's template system provides additional escaping
3. **Defense in depth**: Multiple layers of protection ensure security
4. **Regular updates**: Monitor for CKEditor security updates (currently using 6.7.3)

## Future Considerations

- Consider upgrading to CKEditor 5 (django-ckeditor-5) when available
- Monitor CKEditor security advisories
- Regularly review and update allowed content rules
- Consider adding Content Security Policy (CSP) headers

## References

- [django-ckeditor Documentation](https://github.com/django-ckeditor/django-ckeditor)
- [CKEditor 4 Configuration](https://ckeditor.com/docs/ckeditor4/latest/api/CKEDITOR_config.html)
- [OWASP XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
