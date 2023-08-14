from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()

NUM_POST: int = 13
POSTS_ON_THE_SECOND_PAGE: int = 3
POSTS_ON_THE_PAGE: int = 10


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.author = User.objects.create(username='Barankin')
        cls.group = Group.objects.create(
            title='Тестовая группа_N',
            slug='test-slug_N',
            description='Тестовое описание_N',
        )
        cls.posts = []
        for i in range(NUM_POST):
            cls.posts.append(Post(
                author=cls.author,
                text=f'Тестовы пост {i}',
                group=cls.group,)
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        super().setUp()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), POSTS_ON_THE_PAGE)

    def test_second_page_contains_three_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         POSTS_ON_THE_SECOND_PAGE
                         )
