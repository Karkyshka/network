from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Post

User = get_user_model()

FIRST_OBJECT: int = 0
ONE_FOLLOWER: int = 1


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(username='user')
        cls.user_following = User.objects.create_user(username='user_1')
        cls.post = Post.objects.create(
            author=cls.user_following,
            text='Тестовый текст',
        )

    def setUp(self):
        self.following_client = Client()
        self.follower_client = Client()
        self.following_client.force_login(self.user_following)
        self.follower_client.force_login(self.user_follower)

    def test_follow(self):
        """Зарегистрированный пользователь может подписываться."""
        follower_count = Follow.objects.count()
        self.follower_client.get(reverse(
            'posts:profile_follow',
            args=(self.user_following.username,))
        )
        self.assertEqual(Follow.objects.count(), follower_count + ONE_FOLLOWER)

    def test_unfollow(self):
        """Зарегистрированный пользователь может отписаться."""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        follower_count = Follow.objects.count()
        self.follower_client.get(reverse(
            'posts:profile_unfollow',
            args=(self.user_following.username,))
        )
        self.assertEqual(Follow.objects.count(), follower_count - ONE_FOLLOWER)

    def test_new_post_see_follower(self):
        """Пост появляется в ленте подписавшихся."""
        posts = Post.objects.create(text=self.post.text,
                                    author=self.user_following,)
        follow = Follow.objects.create(user=self.user_follower,
                                       author=self.user_following)
        response = self.follower_client.get(reverse('posts:follow_index'))
        post = response.context['page_obj'][FIRST_OBJECT]
        self.assertEqual(post, posts)
        follow.delete()
