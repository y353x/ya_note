from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from notes.models import Note

User = get_user_model()

ADD_URLS = (
    ('notes:list', None),
    ('notes:add', None),
    ('notes:success', None),
)
LOGIN_URLS = (
    ('notes:home', None),
    ('users:login', None),
    ('users:logout', None),
    ('users:signup', None),
)
EDIT_URLS = (
    'notes:edit',
    'notes:delete',
    'notes:detail'
)


class TestWithoutNote(TestCase):
    """Класс для тестов заметок (без объекта заметки)."""

    NOTE_TEXT = 'Текст заметки'
    NOTE_TITLE = 'Заголовок'
    NOTE_SLUG = 'note_1'
    NEW_NOTE_TEXT = 'Новый текст заметки'
    NEW_NOTE_TITLE = 'Новый заголовок'
    NEW_NOTE_SLUG = 'note_2'

    @classmethod
    def setUpTestData(cls):
        # Автор.
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        # Другой пользователь.
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        # Данные формы для изменения заметки.
        cls.form_data = {
            'title': cls.NEW_NOTE_TITLE,
            'text': cls.NEW_NOTE_TEXT,
            'slug': cls.NEW_NOTE_SLUG,
            'author': cls.author
        }
        # Ссылки работающие без заметки.
        cls.add_url = reverse('notes:add', args=None)
        cls.list_url = reverse('notes:list', args=None)
        cls.success_url = reverse('notes:success', args=None)


class TestWithNote(TestWithoutNote):
    """Класс для тестов заметок (с объектом заметки)."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.note = Note.objects.create(
            title=cls.NOTE_TITLE, text=cls.NOTE_TEXT,
            slug=cls.NOTE_SLUG, author=cls.author
        )
        cls.note_url = reverse('notes:detail', args=(cls.note.slug,))
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
