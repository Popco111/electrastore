import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import requests
from io import BytesIO
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Загружаем предобученную модель ResNet50 (без классификатора, получаем признаки)
resnet = models.resnet50(pretrained=True)
resnet.eval()
# Убираем последний слой классификации, чтобы получать вектор признаков (2048 чисел)
feature_extractor = torch.nn.Sequential(*(list(resnet.children())[:-1]))

preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def get_image_embedding_from_url(url):
    try:
        response = requests.get(url, timeout=5)
        img = Image.open(BytesIO(response.content)).convert('RGB')
        input_tensor = preprocess(img).unsqueeze(0)
        with torch.no_grad():
            embedding = feature_extractor(input_tensor)
        return embedding.squeeze().numpy().flatten()
    except Exception as e:
        return None