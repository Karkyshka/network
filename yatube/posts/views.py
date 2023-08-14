
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import utils


@cache_page(20)
def index(request):
    posts = Post.objects.select_related('author', 'group').all()
    context = utils(posts, request)
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Страница групп"""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('group').all()
    context = {
        'group': group,
        'posts': posts,
    }
    context.update(utils(posts, request))
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Страница пользователя"""
    author = get_object_or_404(User, username=username)
    posts = Post.objects.select_related('group').filter(
        author__username=username)
    following = request.user.is_authenticated and author.following.filter(
        user=request.user).exists()
    context = {
        'author': author,
        'following': following
    }
    context.update(utils(posts, request))
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post_count = Post.objects.select_related('author').filter(
        author=post.author
    ).count()
    title = 'Пост'
    comments = post.comments.all()
    form = CommentForm()
    context = {
        'post_count': post_count,
        'post': post,
        'title': title,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Создание поста"""
    is_edit = False
    form = PostForm(request.POST or None, files=request.FILES or None)
    context = {
        'form': form,
        'is_edit': is_edit
    }
    if not form.is_valid():
        return render(request, 'posts/create_post.html', context)
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', post.author.username)


@login_required
def post_edit(request, post_id):
    """Редактирование поста автором"""
    is_edit = True
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': is_edit,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    """Добавление комментария"""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Лента подписчиков"""
    posts = Post.objects.select_related(
        'author').filter(author__following__user=request.user)
    context = utils(posts, request)
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписка на автора"""
    author = get_object_or_404(User, username=username)
    follower = Follow.objects.filter(user=request.user, author=author)
    if request.user != author and not follower.exists():
        Follow.objects.create(user=request.user, author=author)
    return render(request, 'posts/follow.html')


@login_required
def profile_unfollow(request, username):
    """Отписка от автора"""
    author = get_object_or_404(User, username=username)
    following = Follow.objects.filter(user=request.user, author=author)
    if following.exists():
        following.delete()
    return render(request, 'posts/follow.html')
