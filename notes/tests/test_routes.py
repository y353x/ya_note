# notes/tests/test_routes.py
# Главная страница доступна анонимному пользователю.
# Аутентифицированному пользователю доступна страница со списком
#       заметок notes/, страница успешного добавления заметки done/,
#       страница добавления новой заметки add/.
# Страницы отдельной заметки, удаления и редактирования заметки доступны
#       только автору заметки. Если на эти страницы попытается зайти
#       другой пользователь — вернётся ошибка 404.
# При попытке перейти на страницу списка заметок, страницу
#       успешного добавления записи, страницу добавления заметки,
#       отдельной заметки, редактирования или удаления заметки
#       анонимный пользователь перенаправляется на страницу логина.
# Страницы регистрации пользователей, входа в учётную запись и выхода из неё
#       доступны всем пользователям.
from http import HTTPStatus
from django.test import TestCase
from django.urls import reverse
from notes.models import Note
from django.contrib.auth import get_user_model

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Карл Маркс')
        cls.reader = User.objects.create(username='Фридрих Энгельс')
        cls.note = Note.objects.create(
            title='Заголовок', text='Текст', slug='note_1', author=cls.author
        )

    def test_pages_availability(self):
        """Доступность страниц анонимному пользователю."""
        urls = (
            ('notes:home', None),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_auth_user(self):
        """
        Аутентифицированному пользователю доступна страница со списком
        заметок notes/, страница успешного добавления заметки done/,
        страница добавления новой заметки add/.
        """
        urls = (
            ('notes:list', None),
            ('notes:add', None),
            ('notes:success', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                self.client.force_login(self.author)
                url = reverse(name, args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_user_notes(self):
        """
        Страницы отдельной заметки, удаления и редактирования заметки доступны
        только автору заметки. Если на эти страницы попытается зайти
        другой пользователь — вернётся ошибка 404.
        """
        users_statuses = (
            (self.author, HTTPStatus.OK),  # Для автора - 200.
            (self.reader, HTTPStatus.NOT_FOUND),  # Для читателя - 404.
        )
        for user, status in users_statuses:
            # Логиним пользователя в клиенте:
            self.client.force_login(user)
            # Для каждой пары "пользователь - ожидаемый ответ"
            # перебираем имена тестируемых страниц:
            for name in ('notes:edit', 'notes:delete', 'notes:detail'):
                with self.subTest(user=user, name=name):
                    # Для страницы требуется slug, добавляем в аргумент.
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """
        При попытке перейти на страницу списка заметок, страницу
        успешного добавления записи, страницу добавления заметки,
        отдельной заметки, редактирования или удаления заметки
        анонимный пользователь перенаправляется на страницу логина.
        """
        # Сохраняем адрес страницы логина:
        login_url = reverse('users:login')
        # В цикле перебираем имена страниц, с которых ожидаем редирект:
        for name in ('notes:add', 'notes:list', 'notes:success'):
            with self.subTest(name=name):
                url = reverse(name, args=None)  # args=None - для наглядности.
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                # Проверяем, что редирект приведёт именно на указанную ссылку.
                self.assertRedirects(response, redirect_url)
