# news/tests/test_logic.py
# Залогиненный пользователь может создать заметку, а анонимный — не может.
# Невозможно создать две заметки с одинаковым slug.
# Если при создании заметки не заполнен slug, то он формируется автоматически,
#       с помощью функции pytils.translit.slugify.
# Пользователь может редактировать и удалять свои заметки,
#       но не может редактировать или удалять чужие.
from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from notes.models import Note
from notes.forms import WARNING
from pytils.translit import slugify

User = get_user_model()


class TestNoteCreation(TestCase):
    """Класс для тестов созданий заметок."""
    NEW_NOTE_TEXT = 'Новый текст заметки'
    NEW_NOTE_TITLE = 'Заголовок'
    NEW_NOTE_SLUG = 'note_1'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Карл Маркс')
        cls.reader = User.objects.create(username='Фридрих Энгельс')
        cls.add_url = reverse('notes:add', args=None)

        cls.auth_client = Client()
        cls.auth_client.force_login(cls.author)
        # Данные для POST-запроса при создании комментария.
        cls.form_data = {
            'title': cls.NEW_NOTE_TITLE,
            'text': cls.NEW_NOTE_TEXT,
            'slug': cls.NEW_NOTE_SLUG,
        }
        cls.succes_url = reverse('notes:success', args=None)

    def test_anonymous_user_cant_create_note(self):
        """Анонимный юзер не может создать пост (отправить форму)."""
        # Совершаем запрос от анонимного клиента, в POST-запросе отправляем
        # предварительно подготовленные данные формы с текстом комментария.
        self.client.post(self.add_url, data=self.form_data)
        # Считаем количество заметок.
        notes_count = Note.objects.count()
        # Ожидаем, что заметок в базе нет - сравниваем с нулём.
        self.assertEqual(notes_count, 0)

    def test_user_can_create_note(self):
        """Зарегистрированный юзер может создать пост (отправить форму)."""
        # Совершаем запрос через авторизованный клиент.
        response = self.auth_client.post(self.add_url, data=self.form_data)
        # Проверяем, что редирект привёл к разделу с успешным сообщением.
        self.assertRedirects(response, self.succes_url)
        # Считаем количество заметок.
        notes_count = Note.objects.count()
        # Убеждаемся, что есть одна заметка.
        self.assertEqual(notes_count, 1)
        # Получаем объект заметки из базы.
        note = Note.objects.get()
        # Проверяем, что все атрибуты заметки совпадают с ожидаемыми.
        self.assertEqual(note.title, self.NEW_NOTE_TITLE)
        self.assertEqual(note.text, self.NEW_NOTE_TEXT)
        self.assertEqual(note.slug, self.NEW_NOTE_SLUG)
        self.assertEqual(note.author, self.author)

    def test_not_unique_slug(self):
        """Невозможно создать две заметки с одинаковым slug."""
        self.note = Note.objects.create(
            title='Заголовок', text='Текст', slug='note_1', author=self.author
        )
        # Подменяем slug новой заметки на slug уже существующей записи:
        self.form_data['slug'] = self.note.slug
        response = self.auth_client.post(self.add_url, data=self.form_data)
        # Проверяем, что в ответе содержится ошибка формы для поля slug:
        self.assertFormError(response, 'form', 'slug',
                             errors=(self.note.slug + WARNING))
        # Убеждаемся, что количество заметок в базе осталось равным 1:
        assert Note.objects.count() == 1

    def test_empty_slug(self):
        """
        Если при создании заметки не заполнен slug,
        то он формируется автоматически,
        с помощью функции pytils.translit.slugify.
        """
        # Убираем поле slug из словаря:
        self.form_data.pop('slug')
        response = self.auth_client.post(self.add_url, data=self.form_data)
        # Проверяем, что даже без slug заметка была создана:
        self.assertRedirects(response, self.succes_url)
        assert Note.objects.count() == 1
        # Получаем созданную заметку из базы:
        new_note = Note.objects.get()
        # Формируем ожидаемый slug:
        expected_slug = slugify(self.form_data['title'])
        # Проверяем, что slug заметки соответствует ожидаемому:
        assert new_note.slug == expected_slug


class TestNoteEditDelete(TestCase):
    """Класс для тестов редактирования и удаления заметок."""
    NOTE_TEXT = 'Текст заметки'
    NOTE_TITLE = 'Заголовок'
    NOTE_SLUG = 'note_1'
    NEW_NOTE_TEXT = 'Новый текст заметки'
    NEW_NOTE_TITLE = 'Нрвый заголовок'
    NEW_NOTE_SLUG = 'note_2'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.note = Note.objects.create(
            title=cls.NOTE_TITLE, text=cls.NOTE_TEXT,
            slug=cls.NOTE_SLUG, author=cls.author
        )
        cls.note_url = reverse('notes:detail', args=(cls.note.slug,))

        # Создаём клиент для пользователя-автора.
        cls.author_client = Client()
        # "Логиним" пользователя в клиенте.
        cls.author_client.force_login(cls.author)
        # Делаем всё то же самое для пользователя-читателя.
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

        # URL для редактирования.
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        # URL для удаления.
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        # Формируем данные для POST-запроса по обновлению заметки.
        # cls.form_data = {'text': cls.NEW_NOTE_TEXT}
        cls.form_data = {
            'title': cls.NEW_NOTE_TITLE,
            'text': cls.NEW_NOTE_TEXT,
            'slug': cls.NEW_NOTE_SLUG,
        }
        cls.success_url = reverse('notes:success', args=None)

    def test_author_can_delete_note(self):
        """Пользователь может удалять свои заметки"""
        # От имени автора комментария отправляем DELETE-запрос на удаление.
        response = self.author_client.delete(self.delete_url)
        # Проверяем, что редирект привёл к разделу с комментариями.
        # Заодно проверим статус-коды ответов.
        self.assertRedirects(response, self.success_url)
        # Считаем количество комментариев в системе.
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_author_can_edit_note(self):
        """Автор может редактировать свою заметку."""
        # Выполняем запрос на редактирование от имени автора комментария.
        response = self.author_client.post(self.edit_url, data=self.form_data)
        # Проверяем, что сработал редирект.
        self.assertRedirects(response, self.success_url)
        # Обновляем объект комментария.
        self.note.refresh_from_db()
        # Проверяем, что текст комментария соответствует обновленному.
        self.assertEqual(self.note.title, self.NEW_NOTE_TITLE)
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)
        self.assertEqual(self.note.slug, self.NEW_NOTE_SLUG)

    def test_user_cant_edit_note_of_another_user(self):
        """Пользователь не может редактировать чужие заметки."""
        # Выполняем запрос на редактирование от имени другого пользователя.
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Обновляем.
        self.note.refresh_from_db()
        # Проверяем, что текст остался тем же, что и был.
        self.assertEqual(self.note.text, self.NOTE_TEXT)

    def test_user_cant_delete_note_of_another_user(self):
        """Пользователь не может удалять чужие заметки."""
        response = self.reader_client.delete(self.delete_url)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
