# отдельная заметка передаётся на страницу со списком заметок
#       в списке object_list в словаре context;
# в список заметок одного пользователя не попадают
#       заметки другого пользователя;
# на страницы создания и редактирования заметки передаются формы.
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()


class TestNotesPage(TestCase):
    """Правильность распределения контента."""
    @classmethod
    def setUpTestData(cls):
        Note.objects.create(title='Новость', text='Просто текст.')
        """Класс для тестов редактирования и удаления заметок."""
    NOTE_TEXT = 'Текст заметки'
    NOTE_TITLE = 'Заголовок'
    NOTE_SLUG = 'note_1'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.note = Note.objects.create(
            title=cls.NOTE_TITLE, text=cls.NOTE_TEXT,
            slug=cls.NOTE_SLUG, author=cls.author
        )
        cls.list_url = reverse('notes:list', args=None)
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        # Другой пользователь.
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

    def test_notes_list_for_different_users(self):
        """
        Отдельная заметка передаётся на страницу со списком заметок
        в списке object_list в словаре context;
        в список заметок одного пользователя не попадают
        заметки другого пользователя.
        """
        clients = (
            (self.author_client, True),
            (self.reader_client, False),
        )
        for client, note_in_list in clients:
            with self.subTest(name=clients):
                response = client.get(self.list_url)
                object_list = response.context['object_list']
                self.assertEqual((self.note in object_list), note_in_list)

    def test_pages_contains_form(self):
        """На страницы создания и редактирования заметки передаются формы."""
        url_tuple = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,))
        )
        for name, args in url_tuple:
            with self.subTest(name=name):
                print(args)
                url = reverse(name, args=args)
                response = self.author_client.get(url)
                assert 'form' in response.context
                assert isinstance(response.context['form'], NoteForm)
