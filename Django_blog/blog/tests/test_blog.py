import pytest
from django.urls import reverse

from blog.models import Post


@pytest.mark.django_db
def test_post_str_returns_title():
    post = Post.objects.create(title="Hello", content="World")
    assert str(post) == "Hello"


@pytest.mark.django_db
def test_post_list_view_ok_and_shows_post(client):
    Post.objects.create(title="T1", content="C1")
    res = client.get(reverse("blog:post_list"))
    assert res.status_code == 200
    assert "T1" in res.content.decode("utf-8")


@pytest.mark.django_db
def test_post_detail_view_ok_and_shows_content(client):
    post = Post.objects.create(title="T2", content="C2")
    res = client.get(reverse("blog:post_detail", kwargs={"pk": post.pk}))
    assert res.status_code == 200
    body = res.content.decode("utf-8")
    assert "T2" in body
    assert "C2" in body


@pytest.mark.django_db
def test_post_list_page_renders_template_and_navbar(client):
    res = client.get(reverse("blog:post_list"))
    assert res.status_code == 200
    templates = [template.name for template in res.templates]
    assert "blog/post_list.html" in templates
    assert "Blog" in res.content.decode("utf-8")


@pytest.mark.django_db
def test_post_create_page_renders_form_field(client):
    res = client.get(reverse("blog:post_create"))
    assert res.status_code == 200
    assert 'name="title"' in res.content.decode("utf-8")


@pytest.mark.django_db
def test_post_detail_page_renders_template(client):
    post = Post.objects.create(title="Detail", content="Body")
    res = client.get(reverse("blog:post_detail", kwargs={"pk": post.pk}))
    assert res.status_code == 200
    templates = [template.name for template in res.templates]
    assert "blog/post_detail.html" in templates


@pytest.mark.django_db
def test_post_update_page_renders_current_title(client):
    post = Post.objects.create(title="Current", content="Body")
    res = client.get(reverse("blog:post_update", kwargs={"pk": post.pk}))
    assert res.status_code == 200
    assert "Current" in res.content.decode("utf-8")


@pytest.mark.django_db
def test_post_delete_confirm_page_renders_template(client):
    post = Post.objects.create(title="Delete", content="Body")
    res = client.get(reverse("blog:post_delete", kwargs={"pk": post.pk}))
    assert res.status_code == 200
    templates = [template.name for template in res.templates]
    assert "blog/post_confirm_delete.html" in templates


@pytest.mark.django_db
def test_create_view_creates_post(client):
    res = client.post(
        reverse("blog:post_create"),
        data={"title": "New", "content": "Post"},
    )
    assert res.status_code in (302, 303)
    assert Post.objects.filter(title="New").exists()


@pytest.mark.django_db
def test_update_view_updates_post(client):
    post = Post.objects.create(title="Old", content="Body")
    res = client.post(
        reverse("blog:post_update", kwargs={"pk": post.pk}),
        data={"title": "Updated", "content": "Body"},
    )
    assert res.status_code in (302, 303)
    post.refresh_from_db()
    assert post.title == "Updated"


@pytest.mark.django_db
def test_delete_view_deletes_post(client):
    post = Post.objects.create(title="Del", content="X")
    res = client.post(reverse("blog:post_delete", kwargs={"pk": post.pk}))
    assert res.status_code in (302, 303)
    assert not Post.objects.filter(pk=post.pk).exists()
