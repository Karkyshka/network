from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'name': ('verbose_name')}
        help_texts = {'name': ('Some useful help text.')}


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
