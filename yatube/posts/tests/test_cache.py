from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post

User = get_user_model()

FIRST_OBJECT: int = 0


class СachePagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='willi')
        cls.authorized_client = Client()
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_cache(self):
        """Тест кэша."""
        response = self.authorized_client.get(reverse('posts:index'))
        response_post = response.context['page_obj'][FIRST_OBJECT]
        response_post.delete()
        response_2 = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, response_2.content)
        cache.clear()
        response_3 = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, response_3.content)
