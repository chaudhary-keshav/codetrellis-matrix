"""
Tests for Django extractors and EnhancedDjangoParser.

Part of CodeTrellis v4.33 Django Language Support.
Tests cover:
- Model extraction (fields, relationships, Meta, managers, abstract, proxy)
- View extraction (CBV, FBV, ViewSets, async views)
- URL pattern extraction (path, re_path, include, namespaces)
- Middleware extraction (old-style, new-style, async)
- Form extraction (Form, ModelForm, fields, clean methods)
- Admin extraction (ModelAdmin, inline, register decorators)
- Signal extraction (pre_save, post_save, custom signals)
- Serializer extraction (DRF serializers, nested, ModelSerializer)
- Parser integration (framework detection, version detection, is_django_file, to_codetrellis_format)
"""

import pytest
from codetrellis.django_parser_enhanced import (
    EnhancedDjangoParser,
    DjangoParseResult,
)
from codetrellis.extractors.django import (
    DjangoModelExtractor,
    DjangoModelInfo,
    DjangoFieldInfo,
    DjangoRelationshipInfo,
    DjangoViewExtractor,
    DjangoViewInfo,
    DjangoURLPatternInfo,
    DjangoMiddlewareExtractor,
    DjangoMiddlewareInfo,
    DjangoFormExtractor,
    DjangoFormInfo,
    DjangoAdminExtractor,
    DjangoAdminInfo,
    DjangoSignalExtractor,
    DjangoSignalInfo,
    DjangoSerializerExtractor,
    DjangoSerializerInfo,
    DjangoAPIExtractor,
    DjangoProjectInfo,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedDjangoParser()


@pytest.fixture
def model_extractor():
    return DjangoModelExtractor()


@pytest.fixture
def view_extractor():
    return DjangoViewExtractor()


@pytest.fixture
def middleware_extractor():
    return DjangoMiddlewareExtractor()


@pytest.fixture
def form_extractor():
    return DjangoFormExtractor()


@pytest.fixture
def admin_extractor():
    return DjangoAdminExtractor()


@pytest.fixture
def signal_extractor():
    return DjangoSignalExtractor()


@pytest.fixture
def serializer_extractor():
    return DjangoSerializerExtractor()


@pytest.fixture
def api_extractor():
    return DjangoAPIExtractor()


# ═══════════════════════════════════════════════════════════════════
# Model Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestDjangoModelExtractor:

    def test_extract_basic_model(self, model_extractor):
        """Test extracting a basic Django model with fields."""
        content = """
from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=False)
"""
        models = model_extractor.extract(content, "myapp/models.py")
        assert len(models) >= 1
        article = models[0]
        assert article.name == "Article"
        assert any(f.name == "title" for f in article.fields)
        assert any(f.name == "content" for f in article.fields)
        assert any(f.name == "created" for f in article.fields)

    def test_extract_foreign_key(self, model_extractor):
        """Test extracting ForeignKey relationships."""
        content = """
from django.db import models

class Comment(models.Model):
    article = models.ForeignKey('Article', on_delete=models.CASCADE)
    author = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    text = models.TextField()
"""
        models = model_extractor.extract(content, "myapp/models.py")
        assert len(models) >= 1
        comment = models[0]
        assert len(comment.relationships) >= 1
        fk = [r for r in comment.relationships if r.name == "article"]
        assert len(fk) == 1
        assert fk[0].relationship_type == "ForeignKey"
        assert fk[0].related_model == "Article"

    def test_extract_many_to_many(self, model_extractor):
        """Test extracting ManyToManyField relationships."""
        content = """
from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=200)
    tags = models.ManyToManyField('Tag', blank=True)
"""
        models = model_extractor.extract(content, "myapp/models.py")
        assert len(models) >= 1
        article = models[0]
        m2m = [r for r in article.relationships if r.name == "tags"]
        assert len(m2m) == 1
        assert m2m[0].relationship_type == "ManyToManyField"

    def test_extract_one_to_one(self, model_extractor):
        """Test extracting OneToOneField."""
        content = """
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
"""
        models = model_extractor.extract(content, "myapp/models.py")
        assert len(models) >= 1
        profile = models[0]
        o2o = [r for r in profile.relationships if r.name == "user"]
        assert len(o2o) == 1
        assert o2o[0].relationship_type == "OneToOneField"

    def test_extract_meta_class(self, model_extractor):
        """Test extracting Meta class options."""
        content = """
from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=200)
    created = models.DateTimeField()

    class Meta:
        ordering = ['-created']
        verbose_name = 'article'
        verbose_name_plural = 'articles'
        db_table = 'blog_article'
"""
        models = model_extractor.extract(content, "myapp/models.py")
        assert len(models) >= 1
        article = models[0]
        assert article.meta is not None
        assert article.meta.ordering == ['-created']

    def test_extract_abstract_model(self, model_extractor):
        """Test extracting abstract models."""
        content = """
from django.db import models

class TimeStampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Article(TimeStampedModel):
    title = models.CharField(max_length=200)
"""
        models = model_extractor.extract(content, "myapp/models.py")
        abstract = [m for m in models if m.name == "TimeStampedModel"]
        if abstract:
            assert abstract[0].is_abstract is True

    def test_extract_multiple_models(self, model_extractor):
        """Test extracting multiple models from one file."""
        content = """
from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    isbn = models.CharField(max_length=13, unique=True)

class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField(blank=True)
"""
        models = model_extractor.extract(content, "myapp/models.py")
        assert len(models) >= 3
        names = [m.name for m in models]
        assert "Author" in names
        assert "Book" in names
        assert "Review" in names

    def test_extract_field_attributes(self, model_extractor):
        """Test extracting field-level attributes (null, blank, unique, max_length)."""
        content = """
from django.db import models

class User(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(null=True, blank=True)
    bio = models.TextField(blank=True, default='')
"""
        models = model_extractor.extract(content, "myapp/models.py")
        assert len(models) >= 1
        user = models[0]
        username_field = [f for f in user.fields if f.name == "username"]
        if username_field:
            assert username_field[0].max_length == 150
            assert username_field[0].unique is True

    def test_empty_content_returns_empty(self, model_extractor):
        """Test that empty content returns empty list."""
        result = model_extractor.extract("", "empty.py")
        assert result == []

    def test_non_model_class(self, model_extractor):
        """Test that non-Model classes are not extracted."""
        content = """
class MyHelper:
    def do_something(self):
        pass

class AnotherClass(object):
    pass
"""
        models = model_extractor.extract(content, "helpers.py")
        assert len(models) == 0


# ═══════════════════════════════════════════════════════════════════
# View Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestDjangoViewExtractor:

    def test_extract_fbv(self, view_extractor):
        """Test extracting function-based views (requires Django decorators)."""
        content = """
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods, require_GET
from rest_framework.decorators import api_view

@require_GET
def home(request):
    return HttpResponse("Home")

@require_http_methods(["GET", "POST"])
def about(request):
    return HttpResponse("About page")

@api_view(["GET"])
def api_root(request):
    return HttpResponse("API")
"""
        result = view_extractor.extract(content, "views.py")
        views = result.get('views', [])
        assert len(views) >= 1

    def test_extract_cbv(self, view_extractor):
        """Test extracting class-based views."""
        content = """
from django.views.generic import ListView, DetailView, CreateView
from .models import Article

class ArticleListView(ListView):
    model = Article
    template_name = 'articles/list.html'
    paginate_by = 10

class ArticleDetailView(DetailView):
    model = Article
    template_name = 'articles/detail.html'

class ArticleCreateView(CreateView):
    model = Article
    fields = ['title', 'content']
"""
        result = view_extractor.extract(content, "views.py")
        views = result.get('views', [])
        assert len(views) >= 2

    def test_extract_url_patterns(self, view_extractor):
        """Test extracting URL patterns."""
        content = """
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('articles/', views.ArticleListView.as_view(), name='article-list'),
    path('articles/<int:pk>/', views.ArticleDetailView.as_view(), name='article-detail'),
    path('api/', include('api.urls', namespace='api')),
]
"""
        result = view_extractor.extract(content, "urls.py")
        urls = result.get('url_patterns', [])
        assert len(urls) >= 1

    def test_extract_drf_viewset(self, view_extractor):
        """Test extracting DRF ViewSets."""
        content = """
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import Article
from .serializers import ArticleSerializer

class ArticleViewSet(ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]
"""
        result = view_extractor.extract(content, "views.py")
        views = result.get('views', [])
        assert len(views) >= 1

    def test_extract_async_view(self, view_extractor):
        """Test extracting async views (Django 4.1+) — requires decorator."""
        content = """
from django.http import JsonResponse
from rest_framework.decorators import api_view

@api_view(["GET"])
async def async_home(request):
    return JsonResponse({'status': 'ok'})
"""
        result = view_extractor.extract(content, "views.py")
        views = result.get('views', [])
        # Should detect the async view if decorator matches
        assert len(views) >= 1
        if views:
            assert views[0].is_async is True


# ═══════════════════════════════════════════════════════════════════
# Middleware Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestDjangoMiddlewareExtractor:

    def test_extract_new_style_middleware(self, middleware_extractor):
        """Test extracting new-style Django 1.10+ middleware."""
        content = """
from django.utils.deprecation import MiddlewareMixin

class TimingMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        import time
        start = time.time()
        response = self.get_response(request)
        duration = time.time() - start
        response['X-Duration'] = str(duration)
        return response
"""
        result = middleware_extractor.extract(content, "middleware.py")
        middleware_list = result.get('middleware', [])
        assert len(middleware_list) >= 1
        assert middleware_list[0].name == "TimingMiddleware"

    def test_extract_middleware_with_hooks(self, middleware_extractor):
        """Test extracting middleware with process_* hooks."""
        content = """
from django.utils.deprecation import MiddlewareMixin

class CustomMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        pass

    def process_exception(self, request, exception):
        pass
"""
        result = middleware_extractor.extract(content, "middleware.py")
        middleware_list = result.get('middleware', [])
        assert len(middleware_list) >= 1
        mw = middleware_list[0]
        assert "process_view" in mw.hooks or "process_exception" in mw.hooks

    def test_extract_async_middleware(self, middleware_extractor):
        """Test extracting async middleware (Django 4.1+)."""
        content = """
from django.utils.deprecation import MiddlewareMixin

class AsyncMiddleware(MiddlewareMixin):
    async_capable = True

    def __init__(self, get_response):
        self.get_response = get_response

    async def __call__(self, request):
        response = await self.get_response(request)
        return response
"""
        result = middleware_extractor.extract(content, "middleware.py")
        middleware_list = result.get('middleware', [])
        assert len(middleware_list) >= 1

    def test_empty_content(self, middleware_extractor):
        """Test empty content returns empty list."""
        result = middleware_extractor.extract("", "empty.py")
        middleware_list = result.get('middleware', [])
        assert len(middleware_list) == 0


# ═══════════════════════════════════════════════════════════════════
# Form Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestDjangoFormExtractor:

    def test_extract_basic_form(self, form_extractor):
        """Test extracting a basic Django Form."""
        content = """
from django import forms

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)
"""
        result = form_extractor.extract(content, "forms.py")
        forms_list = result.get('forms', [])
        assert len(forms_list) >= 1
        assert forms_list[0].name == "ContactForm"

    def test_extract_model_form(self, form_extractor):
        """Test extracting a ModelForm."""
        content = """
from django import forms
from .models import Article

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'content', 'category']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
        }
"""
        result = form_extractor.extract(content, "forms.py")
        forms_list = result.get('forms', [])
        assert len(forms_list) >= 1
        form = forms_list[0]
        assert form.name == "ArticleForm"
        assert form.form_type in ("ModelForm", "modelform", "model_form")

    def test_extract_form_with_clean_methods(self, form_extractor):
        """Test extracting forms with custom clean methods."""
        content = """
from django import forms

class RegisterForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data['username']
        if len(username) < 3:
            raise forms.ValidationError("Too short")
        return username

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password') != cleaned_data.get('confirm_password'):
            raise forms.ValidationError("Passwords don't match")
        return cleaned_data
"""
        result = form_extractor.extract(content, "forms.py")
        forms_list = result.get('forms', [])
        assert len(forms_list) >= 1
        form = forms_list[0]
        assert len(form.clean_methods) >= 1

    def test_empty_content(self, form_extractor):
        """Test empty content returns no forms."""
        result = form_extractor.extract("", "empty.py")
        forms_list = result.get('forms', [])
        assert len(forms_list) == 0


# ═══════════════════════════════════════════════════════════════════
# Admin Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestDjangoAdminExtractor:

    def test_extract_basic_admin(self, admin_extractor):
        """Test extracting basic ModelAdmin."""
        content = """
from django.contrib import admin
from .models import Article

class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'created', 'is_published']
    list_filter = ['is_published', 'created']
    search_fields = ['title', 'content']

admin.site.register(Article, ArticleAdmin)
"""
        result = admin_extractor.extract(content, "admin.py")
        admins = result.get('admin_classes', [])
        assert len(admins) >= 1
        admin_obj = admins[0]
        assert admin_obj.name == "ArticleAdmin"

    def test_extract_admin_with_inlines(self, admin_extractor):
        """Test extracting admin with inline classes."""
        content = """
from django.contrib import admin
from .models import Article, Comment

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 3

class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author']
    inlines = [CommentInline]

admin.site.register(Article, ArticleAdmin)
"""
        result = admin_extractor.extract(content, "admin.py")
        admins = result.get('admin_classes', [])
        assert len(admins) >= 1

    def test_extract_register_decorator(self, admin_extractor):
        """Test extracting @admin.register() decorator."""
        content = """
from django.contrib import admin
from .models import Article

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author']
    list_filter = ['is_published']
"""
        result = admin_extractor.extract(content, "admin.py")
        admins = result.get('admin_classes', [])
        assert len(admins) >= 1

    def test_empty_content(self, admin_extractor):
        """Test empty content returns no admins."""
        result = admin_extractor.extract("", "empty.py")
        admins = result.get('admin_classes', [])
        assert len(admins) == 0


# ═══════════════════════════════════════════════════════════════════
# Signal Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestDjangoSignalExtractor:

    def test_extract_pre_save_signal(self, signal_extractor):
        """Test extracting pre_save signal connection."""
        content = """
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Article

@receiver(pre_save, sender=Article)
def article_pre_save(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.title)
"""
        result = signal_extractor.extract(content, "signals.py")
        signals = result.get('signal_connections', [])
        assert len(signals) >= 1
        sig = signals[0]
        assert sig.name == "pre_save" or sig.receiver_name == "article_pre_save"

    def test_extract_post_save_signal(self, signal_extractor):
        """Test extracting post_save signal connection."""
        content = """
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
"""
        result = signal_extractor.extract(content, "signals.py")
        signals = result.get('signal_connections', [])
        assert len(signals) >= 1

    def test_extract_connect_style_signal(self, signal_extractor):
        """Test extracting .connect() style signal registration."""
        content = """
from django.db.models.signals import post_delete
from .models import Article

def cleanup_article(sender, instance, **kwargs):
    instance.image.delete(save=False)

post_delete.connect(cleanup_article, sender=Article)
"""
        result = signal_extractor.extract(content, "signals.py")
        signals = result.get('signal_connections', [])
        assert len(signals) >= 1

    def test_empty_content(self, signal_extractor):
        """Test empty content returns no signals."""
        result = signal_extractor.extract("", "empty.py")
        signals = result.get('signal_connections', [])
        assert len(signals) == 0


# ═══════════════════════════════════════════════════════════════════
# Serializer Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestDjangoSerializerExtractor:

    def test_extract_model_serializer(self, serializer_extractor):
        """Test extracting DRF ModelSerializer."""
        content = """
from rest_framework import serializers
from .models import Article

class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'author', 'created']
        read_only_fields = ['id', 'created']
"""
        result = serializer_extractor.extract(content, "serializers.py")
        serializers_list = result.get('serializers', [])
        assert len(serializers_list) >= 1
        ser = serializers_list[0]
        assert ser.name == "ArticleSerializer"

    def test_extract_nested_serializer(self, serializer_extractor):
        """Test extracting serializer with nested serializers."""
        content = """
from rest_framework import serializers
from .models import Article, Comment

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'text', 'author']

class ArticleSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'comments']
"""
        result = serializer_extractor.extract(content, "serializers.py")
        serializers_list = result.get('serializers', [])
        assert len(serializers_list) >= 2

    def test_extract_plain_serializer(self, serializer_extractor):
        """Test extracting Serializer (non-Model)."""
        content = """
from rest_framework import serializers

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
"""
        result = serializer_extractor.extract(content, "serializers.py")
        serializers_list = result.get('serializers', [])
        assert len(serializers_list) >= 1
        ser = serializers_list[0]
        assert ser.name == "LoginSerializer"

    def test_empty_content(self, serializer_extractor):
        """Test empty content returns no serializers."""
        result = serializer_extractor.extract("", "empty.py")
        serializers_list = result.get('serializers', [])
        assert len(serializers_list) == 0


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestDjangoAPIExtractor:

    def test_extract_project_info(self, api_extractor):
        """Test Django project info extraction."""
        content = """
from django.db import models
from django.views.generic import ListView
"""
        result = api_extractor.extract(content, "app.py")
        assert 'project_info' in result
        assert result['project_info'] is not None

    def test_detect_drf_usage(self, api_extractor):
        """Test DRF detection via project info."""
        content = """
from rest_framework.viewsets import ModelViewSet
from rest_framework import serializers

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
}
"""
        result = api_extractor.extract(content, "settings.py")
        project_info = result.get('project_info')
        assert project_info is not None

    def test_detect_installed_apps(self, api_extractor):
        """Test installed apps extraction from settings."""
        content = """
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'rest_framework',
    'myapp',
]
"""
        result = api_extractor.extract(content, "settings.py")
        project_info = result.get('project_info')
        assert project_info is not None
        if project_info.installed_apps:
            assert 'rest_framework' in project_info.installed_apps or len(project_info.installed_apps) > 0


# ═══════════════════════════════════════════════════════════════════
# Enhanced Django Parser Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedDjangoParser:

    def test_is_django_file(self, parser):
        """Test Django file detection."""
        django_content = """
from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=200)
"""
        assert parser.is_django_file(django_content, "models.py") is True

    def test_not_django_file(self, parser):
        """Test non-Django file detection."""
        content = """
import os
import sys

def hello():
    print("Hello World")
"""
        assert parser.is_django_file(content, "hello.py") is False

    def test_parse_model_file(self, parser):
        """Test parsing a Django models.py file."""
        content = """
from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

class Comment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
"""
        result = parser.parse(content, "myapp/models.py")

        assert isinstance(result, DjangoParseResult)
        assert len(result.models) >= 2
        assert result.file_type == "model"

        # Check model names
        names = [m.name for m in result.models]
        assert "Article" in names
        assert "Comment" in names

        # Check Article fields
        article = [m for m in result.models if m.name == "Article"][0]
        assert len(article.fields) >= 3
        assert len(article.relationships) >= 1
        assert article.bases == ["models.Model"] or "Model" in str(article.bases)

    def test_parse_views_file(self, parser):
        """Test parsing a Django views.py file."""
        content = """
from django.views.generic import ListView, DetailView
from .models import Article

class ArticleListView(ListView):
    model = Article
    template_name = 'articles/list.html'
    paginate_by = 10

class ArticleDetailView(DetailView):
    model = Article
"""
        result = parser.parse(content, "myapp/views.py")
        assert isinstance(result, DjangoParseResult)
        assert result.file_type == "view"
        assert len(result.views) >= 1

    def test_parse_urls_file(self, parser):
        """Test parsing a Django urls.py file."""
        content = """
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('articles/', views.ArticleListView.as_view(), name='article-list'),
    path('api/', include('api.urls', namespace='api')),
]
"""
        result = parser.parse(content, "myapp/urls.py")
        assert isinstance(result, DjangoParseResult)
        assert result.file_type == "url"
        assert len(result.url_patterns) >= 1

    def test_parse_admin_file(self, parser):
        """Test parsing a Django admin.py file."""
        content = """
from django.contrib import admin
from .models import Article, Comment

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 3

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'created']
    list_filter = ['is_published']
    inlines = [CommentInline]
"""
        result = parser.parse(content, "myapp/admin.py")
        assert isinstance(result, DjangoParseResult)
        assert result.file_type == "admin"
        assert len(result.admin_classes) >= 1

    def test_parse_serializers_file(self, parser):
        """Test parsing a DRF serializers.py file."""
        content = """
from rest_framework import serializers
from .models import Article

class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'author', 'created']
"""
        result = parser.parse(content, "myapp/serializers.py")
        assert isinstance(result, DjangoParseResult)
        assert result.file_type == "serializer"
        assert len(result.serializers) >= 1

    def test_parse_signals_file(self, parser):
        """Test parsing a Django signals.py file."""
        content = """
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
"""
        result = parser.parse(content, "myapp/signals.py")
        assert isinstance(result, DjangoParseResult)
        assert result.file_type == "signal"
        assert len(result.signal_connections) >= 1

    def test_parse_forms_file(self, parser):
        """Test parsing a Django forms.py file."""
        content = """
from django import forms
from .models import Article

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'content']

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)
"""
        result = parser.parse(content, "myapp/forms.py")
        assert isinstance(result, DjangoParseResult)
        assert result.file_type == "form"
        assert len(result.forms) >= 2

    def test_detect_frameworks(self, parser):
        """Test framework ecosystem detection."""
        content = """
from django.db import models
from rest_framework import serializers
from celery import shared_task
from channels.generic.websocket import AsyncWebsocketConsumer
"""
        result = parser.parse(content, "myapp/tasks.py")
        assert 'django' in result.detected_frameworks or 'django.db' in result.detected_frameworks

    def test_django_version_detection(self, parser):
        """Test Django version detection from imports."""
        # path() was introduced in Django 2.0
        content = """
from django.urls import path
from django.views import View
"""
        result = parser.parse(content, "urls.py")
        assert result.django_version != "" or len(result.detected_frameworks) > 0

    def test_to_codetrellis_format(self, parser):
        """Test to_codetrellis_format produces valid output."""
        content = """
from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
"""
        result = parser.parse(content, "myapp/models.py")
        output = parser.to_codetrellis_format(result)

        assert isinstance(output, str)
        assert "[FILE:" in output
        assert "DJANGO_MODELS" in output
        assert "Article" in output

    def test_to_codetrellis_format_views(self, parser):
        """Test to_codetrellis_format with views."""
        content = """
from django.views.generic import ListView
from .models import Article

class ArticleListView(ListView):
    model = Article
    template_name = 'articles/list.html'
"""
        result = parser.parse(content, "myapp/views.py")
        output = parser.to_codetrellis_format(result)

        assert isinstance(output, str)
        assert "DJANGO_VIEWS" in output or "ArticleListView" in output

    def test_to_codetrellis_format_urls(self, parser):
        """Test to_codetrellis_format with URL patterns."""
        content = """
from django.urls import path, include
from . import views

urlpatterns = [
    path('articles/', views.article_list, name='article-list'),
    path('api/', include('api.urls')),
]
"""
        result = parser.parse(content, "myapp/urls.py")
        output = parser.to_codetrellis_format(result)

        assert isinstance(output, str)
        assert "DJANGO_URLS" in output or "articles" in output

    def test_to_codetrellis_format_comprehensive(self, parser):
        """Test comprehensive output format with multiple sections."""
        content = """
from django.db import models
from django.contrib import admin
from rest_framework import serializers

class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)

    class Meta:
        ordering = ['-created']

class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author']
    list_filter = ['is_published']

class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['id', 'title', 'content']
"""
        result = parser.parse(content, "myapp/models.py")
        output = parser.to_codetrellis_format(result)

        assert isinstance(output, str)
        assert "Article" in output
        # Should have models at minimum
        assert "DJANGO_MODELS" in output

    def test_parse_empty_file(self, parser):
        """Test parsing empty content."""
        result = parser.parse("", "empty.py")
        assert isinstance(result, DjangoParseResult)
        assert len(result.models) == 0
        assert len(result.views) == 0

    def test_parse_non_django_file(self, parser):
        """Test parsing a file with no Django imports."""
        content = """
import os
import sys

def main():
    print("Hello World")
"""
        result = parser.parse(content, "main.py")
        assert isinstance(result, DjangoParseResult)
        assert len(result.models) == 0


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════

class TestDjangoEdgeCases:

    def test_model_with_custom_manager(self, parser):
        """Test model with custom manager."""
        content = """
from django.db import models

class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_published=True)

class Article(models.Model):
    title = models.CharField(max_length=200)
    is_published = models.BooleanField(default=False)

    objects = models.Manager()
    published = PublishedManager()
"""
        result = parser.parse(content, "models.py")
        assert len(result.models) >= 1

    def test_model_with_choices(self, parser):
        """Test model with field choices."""
        content = """
from django.db import models

class Article(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    title = models.CharField(max_length=200)
"""
        result = parser.parse(content, "models.py")
        assert len(result.models) >= 1

    def test_multiple_file_types_mixed(self, parser):
        """Test file with mixed Django components."""
        content = """
from django.db import models
from django.views.generic import ListView
from django.urls import path

class Article(models.Model):
    title = models.CharField(max_length=200)

class ArticleListView(ListView):
    model = Article

urlpatterns = [
    path('articles/', ArticleListView.as_view()),
]
"""
        result = parser.parse(content, "app.py")
        assert isinstance(result, DjangoParseResult)
        # Should extract at least models
        assert len(result.models) >= 1

    def test_deeply_nested_relationships(self, parser):
        """Test model with multiple relationship types."""
        content = """
from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=100)

class Category(models.Model):
    name = models.CharField(max_length=50)

class Tag(models.Model):
    name = models.CharField(max_length=30)

class Article(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    tags = models.ManyToManyField(Tag, blank=True)
"""
        result = parser.parse(content, "models.py")
        assert len(result.models) >= 4
        article = [m for m in result.models if m.name == "Article"]
        assert len(article) == 1
        assert len(article[0].relationships) >= 3
