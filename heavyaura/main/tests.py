import pytest
from django.urls import reverse
from django.test import Client
from .models import Category, Product


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def category(db):
    return Category.objects.create(name="Test Category", slug="test-category")


@pytest.fixture
def products(db, category):
    return [
        Product.objects.create(
            category=category,
            name="Product 1",
            slug="product-1",
            price=50.00,
            available=True,
            discount=5.0,
        ),
        Product.objects.create(
            category=category,
            name="Product 2",
            slug="product-2",
            price=150.00,
            available=True,
            discount=10.0,
        ),
        Product.objects.create(
            category=category,
            name="Product 3",
            slug="product-3",
            price=100.00,
            available=True,
            discount=0.0,
        ),
        Product.objects.create(
            category=category,
            name="Product 4",
            slug="product-4",
            price=200.00,
            available=True,
            discount=15.0,
        ),
    ]


@pytest.mark.django_db
def test_popular_list_view(client, products):
    response = client.get(reverse("main:popular_list"))
    assert response.status_code == 200
    assert "products" in response.context
    sorted_products = sorted(products, key=lambda p: p.price, reverse=True)[:3]
    assert list(response.context["products"]) == sorted_products


@pytest.mark.django_db
def test_product_detail_view(client, products):
    product = products[0]
    response = client.get(reverse("main:product_detail", args=[product.slug]))
    assert response.status_code == 200
    assert "product" in response.context
    assert response.context["product"].name == product.name
    assert "cart_product_form" in response.context


@pytest.mark.django_db
def test_product_list_view(client, category, products):
    response = client.get(
        reverse("main:product_list_by_category", args=[category.slug])
    )
    assert response.status_code == 200
    assert "products" in response.context
    for product in products:
        assert product in response.context["products"]


@pytest.mark.django_db
def test_product_str(products):
    assert str(products[0]) == "Product 1"


@pytest.mark.django_db
def test_product_get_absolute_url(products):
    assert products[0].get_absolute_url() == f"/shop/{products[0].slug}/"


@pytest.mark.django_db
def test_product_sell_price(products):
    assert products[0].sell_price() == 47.50


@pytest.mark.django_db
def test_product_list_pagination(client, category):
    for i in range(15):
        Product.objects.create(
            category=category,
            name=f"Product {i}",
            slug=f"product-{i}",
            price=10.00,
            available=True,
        )

    response = client.get(reverse("main:product_list"))
    assert response.status_code == 200
    assert "products" in response.context
    assert len(response.context["products"]) == 10

    response = client.get(reverse("main:product_list") + "?page=2")
    assert response.status_code == 200
    assert len(response.context["products"]) == 5


@pytest.mark.django_db
def test_category_contains_only_its_products(client, category, products):
    category2 = Category.objects.create(
        name="Another Category", slug="another-category"
    )

    other_products = [
        Product.objects.create(
            category=category2,
            name="Other Product 1",
            slug="other-product-1",
            price=100.00,
            available=True,
        ),
        Product.objects.create(
            category=category2,
            name="Other Product 2",
            slug="other-product-2",
            price=150.00,
            available=True,
        ),
    ]

    response = client.get(
        reverse("main:product_list_by_category", args=[category.slug])
    )

    assert response.status_code == 200
    assert "products" in response.context

    for product in response.context["products"]:
        assert product.category == category

    for product in other_products:
        assert product not in response.context["products"]


@pytest.mark.django_db
def test_product_detail_not_found(client):
    response = client.get(reverse("main:product_detail", args=["non-existent-product"]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_category_not_found(client):
    response = client.get(
        reverse("main:product_list_by_category", args=["invalid-category"])
    )
    assert response.status_code == 404
