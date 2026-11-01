import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import requests
from io import BytesIO
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from django.shortcuts import render, get_object_or_404
from .models import Product, Category

def product_list_view(request):
    """Отображение страницы со списком товаров (каталог)"""
    return render(request, 'product_list.html')

def product_detail_view(request, pk):
    """Отображение страницы конкретного товара по ID"""
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'product_detail.html', {'product': product})

# --- 1. Компьютерное зрение (ResNet50 для картинок) ---
# Загружаем модель один раз при старте
resnet = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
resnet.eval()
# Берем вектор признаков до слоя классификации
feature_extractor = torch.nn.Sequential(*(list(resnet.children())[:-1]))

preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def get_image_vector(image_url):
    """Преобразует изображение по URL в вектор признаков."""
    try:
        response = requests.get(image_url, timeout=5)
        img = Image.open(BytesIO(response.content)).convert('RGB')
        input_tensor = preprocess(img).unsqueeze(0)
        with torch.no_grad():
            embedding = feature_extractor(input_tensor)
        return embedding.squeeze().numpy().flatten()
    except Exception:
        return None

# --- 2. Анализ текста и отзывов (TF-IDF + Cosine Similarity) ---
def find_text_similar_products(target_product, all_products, top_n=4):
    """Находит похожие товары на основе описания и текстов отзывов."""
    if not all_products:
        return []

    documents = []
    product_list = list(all_products)

    for prod in product_list:
        # Собираем все отзывы товара в один текст
        reviews_text = " ".join([r.comment for r in prod.reviews.all()])
        full_text = f"{prod.title} {prod.description} {reviews_text}"
        documents.append(full_text)

    # Строим TF-IDF матрицу
    vectorizer = TfidfVectorizer(stop_words=None)
    tfidf_matrix = vectorizer.fit_transform(documents)

    # Находим индекс целевого товара
    target_idx = product_list.index(target_product)

    # Считаем сходство со всеми товарами
    cosine_sim = cosine_similarity(tfidf_matrix[target_idx], tfidf_matrix).flatten()

    # Сортируем и исключаем сам целевой товар
    related_indices = cosine_sim.argsort()[::-1]
    related_indices = [i for i in related_indices if i != target_idx][:top_n]

    return [product_list[i] for i in related_indices]