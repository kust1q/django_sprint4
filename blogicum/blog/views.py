from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from .models import Post, Category, Comment
from .forms import PostForm, CommentForm, UserRegistrationForm, UserEditForm

POSTSCOUNT = 10

User = get_user_model()


def _paginate(request, queryset):
    paginator = Paginator(queryset, POSTSCOUNT)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def _published_posts_filter():
    return (
        Q(pub_date__lte=timezone.now())
        & Q(is_published=True)
        & Q(category__is_published=True)
    )


class IndexView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'page_obj'
    paginate_by = 10

    def get_queryset(self):
        return (
            Post.objects
            .filter(_published_posts_filter())
            .select_related('location', 'author', 'category')
            .order_by('-pub_date')
            .annotate(comment_count=Count('comments'))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


def post_detail(request, id):
    template = 'blog/detail.html'
    q = Post.objects.select_related('category', 'location', 'author')
    if request.user.is_authenticated:
        query = q.filter(Q(author=request.user) | _published_posts_filter())
    else:
        query = q.filter(_published_posts_filter())
    post = get_object_or_404(query, id=id)
    comments = (
        Comment.objects.select_related('author')
        .filter(post=post)
        .order_by('created_at')
    )
    context = {
        'post': post
    }
    form = CommentForm()
    context = {'post': post, 'comments': comments, 'form': form}
    return render(request, template, context)


def category_posts(request, category_slug):
    template = 'blog/category.html'
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )

    posts = (
        Post.objects.select_related('location', 'author')
        .filter(category=category)
        .filter(_published_posts_filter())
        .annotate(comment_count=Count('comments'))
        .order_by('-pub_date')
    )

    page_obj = _paginate(request, posts)

    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'blog/profile.html'
    User = get_user_model()
    profile_user = get_object_or_404(User, username=username)
    posts = (
        Post.objects
        .select_related('category', 'location', 'author')
        .filter(author=profile_user)
    )
    if request.user != profile_user:
        posts = posts.filter(_published_posts_filter())
    posts = (
        posts.annotate(comment_count=Count('comments'))
        .order_by('-pub_date')
    )
    page_obj = _paginate(request, posts)
    context = {'profile': profile_user, 'page_obj': page_obj}
    return render(request, template, context)


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserEditForm
    template_name = 'blog/user.html'
    login_url = reverse_lazy('login')

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('blog:profile',
                            kwargs={'username': self.request.user.username})


def register(request):
    template = 'registration/registration_form.html'
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, template, {'form': form})


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    login_url = reverse_lazy('login')\


    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:profile',
                            kwargs={'username': self.request.user.username})


@login_required
def post_edit(request, id):
    template = 'blog/create.html'
    post = get_object_or_404(Post, id=id)
    if post.author != request.user:
        return redirect('blog:post_detail', id=post.id)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', id=post.id)
    else:
        form = PostForm(instance=post)
    return render(request, template, {'form': form})


@login_required
def post_delete(request, id):
    template = 'blog/create.html'
    post = get_object_or_404(Post, id=id, author=request.user)
    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)
    form = PostForm(instance=post)
    return render(request, template, {'form': form})


@login_required
def add_comment(request, post_id):
    q = Post.objects.select_related('category', 'location', 'author')
    if request.user.is_authenticated:
        query = q.filter(Q(author=request.user) | _published_posts_filter())
    else:
        query = q.filter(_published_posts_filter())
    post = get_object_or_404(query, id=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', id=post.id)


@login_required
def edit_comment(request, post_id, comment_id):
    template = 'blog/comment.html'
    comment = get_object_or_404(
        Comment,
        id=comment_id,
        post_id=post_id,
        author=request.user
    )
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', id=post_id)
    else:
        form = CommentForm(instance=comment)
    context = {'form': form, 'comment': comment, 'post': comment.post}
    return render(request, template, context)


@login_required
def delete_comment(request, post_id, comment_id):
    template = 'blog/comment.html'
    comment = get_object_or_404(
        Comment,
        id=comment_id,
        post_id=post_id,
        author=request.user
    )
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', id=post_id)
    context = {'comment': comment, 'post': comment.post}
    return render(request, template, context)
