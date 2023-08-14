import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()
ONE_POST: int = 1
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.user = User.objects.create_user(username='willi')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(title='Тестовая группа',
                                          slug='test-group',
                                          description='Описание')

        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def check_forms(self, post, form_data):
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.id, form_data['group'])

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='Котик.jpeg',
            content=image,
            content_type='image/png'
        )
        post_content = {
            'text': 'Текст записанный в форму',
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'), data=post_content, follow=True
        )
        post = Post.objects.first()
        self.assertEqual(post.image.name, f'posts/{uploaded.name}')
        self.check_forms(post, post_content)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(),
                         posts_count + ONE_POST)

    def test_post_edit(self):
        """Валидная форма изменяет запись в Post."""
        created_post = Post.objects.create(
            text='Оригинальный текст',
            author=self.user,
            group=self.group
        )
        post_edited_form = {
            'text': 'Редактируем текст',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': created_post.id}),
            data=post_edited_form
        )
        edited_post = Post.objects.filter(id=created_post.id).get()
        self.check_forms(edited_post, post_edited_form)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_add_comment_authorized(self):
        """Комментировать посты может только авторизованный пользователь"""
        self.post = Post.objects.create(author=self.user)
        form_data = {'text': 'text'}
        response = self.client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, f"/auth/login/?next=/posts/{self.post.pk}/comment/"
        )
