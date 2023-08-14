import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

FIRST_OBJECT: int = 0
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='willi')
        cls.user_creator = User.objects.create(username='User')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image_name = 'image.jpg'
        cls.uploaded = SimpleUploadedFile(
            name=cls.image_name,
            content=image,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user_creator,
            text="комментарий",
        )

    def setUp(self):
        super().setUp()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def check_post(self, post):
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.image.name, f'posts/{self.uploaded}')

    def test_index_show_correct_context(self):
        """Список постов в index."""
        response = self.client.get(reverse('posts:index'))
        post = response.context['page_obj'][FIRST_OBJECT]
        self.check_post(post)

    def test_group_list_show_correct_context(self):
        """Список постов в group_list."""
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}))
        post = response.context['page_obj'][FIRST_OBJECT]
        self.check_post(post)

    def test_profile_show_correct_context(self):
        """Список постов в profile."""
        response = self.authorized_client.get(
            reverse('posts:profile', args=(self.post.author,))
        )
        post = response.context['page_obj'][FIRST_OBJECT]
        self.check_post(post)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail."""
        response = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        post = response.context.get('post')
        test_comment = response.context['comments'][FIRST_OBJECT]
        self.assertEqual(test_comment, self.comment)
        self.check_post(post)

    def test_create_edit_show_correct_context(self):
        """Шаблон create_edit редактирования поста."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_show_correct_context(self):
        """Шаблон create_edit создание поста."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_check_group_in_index(self):
        """Проверяем создание нового поста
        на главной странице сайта
        на странице выбранной группы
        в профайле пользователя
        """
        form_fields = {
            reverse('posts:index'): Post.objects.get(group=self.post.group),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                Post.objects.get(group=self.post.group),
            reverse('posts:profile', kwargs={'username': self.post.author}):
                Post.objects.get(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context['page_obj']
                self.assertIn(expected, form_field)

    def test_check_group_not_in_mistake_group_list_page(self):
        """
        Проверяем, что этот пост не попал в группу,
        для которой не был предназначен.
        """
        form_fields = {
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                Post.objects.exclude(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context['page_obj']
                self.assertNotIn(expected, form_field)
