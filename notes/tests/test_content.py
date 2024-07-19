# отдельная заметка передаётся на страницу со списком заметок
#       в списке object_list в словаре context;
# в список заметок одного пользователя не попадают
#       заметки другого пользователя;
# на страницы создания и редактирования заметки передаются формы.
from django.urls import reverse
from notes.forms import NoteForm
from .common import TestWithNote


class TestNotesPage(TestWithNote):
    """Правильность распределения контента."""

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
                url = reverse(name, args=args)
                response = self.author_client.get(url)
                assert 'form' in response.context
                assert isinstance(response.context['form'], NoteForm)
