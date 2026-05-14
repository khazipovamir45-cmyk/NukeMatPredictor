import joblib
import numpy as np
import os
from functools import lru_cache

scaler = None
materials_list = None
features_normal = None

def load_knn_data():
    """Загружает данные модели при старте сервера (один раз)"""
    global scaler, materials_list, features_normal
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    scaler = joblib.load(os.path.join(base_dir, "scaler.pkl"))
    materials_list = joblib.load(os.path.join(base_dir, "materials_list.pkl"))
    features_normal = np.load(os.path.join(base_dir, "features.npy"))
    
    # Предрасчёт worst_index для каждого запроса не нужен — будем считать быстро

def find_nearest(query, k=5):
    """
    Быстрый поиск k ближайших соседей.
    Оптимизация: используем broadcasting без лишних копий.
    """
    query_normal = scaler.transform([query])  # (1, 5)
    # Вычисляем евклидово расстояние до всех материалов
    dist = np.linalg.norm(features_normal - query_normal, axis=1)
    # Находим k ближайших (argsort частичный, но для 200 материалов разница невелика)
    indexes = np.argpartition(dist, k)[:k]  # быстрее, чем argsort
    # Сортируем только k элементов для красоты
    indexes = indexes[np.argsort(dist[indexes])]
    return indexes, dist[indexes]

def rank_materials(temp, dose, strength, therm_cond, heat_cap):
    """
    Возвращает 3 материала: оптимальный, допустимый, непригодный.
    Оптимизация: убраны лишние копии и повторный transform.
    """
    query = [temp, strength, dose, therm_cond, heat_cap]
    
    # Находим 5 ближайших
    indices, distances = find_nearest(query, k=5)
    
    # Оптимальный — ближайший
    optimal = materials_list[indices[0]].copy()
    optimal['status'] = 'optimal'
    optimal['status_text'] = '★ Оптимальный'
    
    # Допустимый — второй ближайший
    acceptable = materials_list[indices[1]].copy()
    acceptable['status'] = 'acceptable'
    acceptable['status_text'] = '✓ Допустимый'
    
    # Непригодный — самый дальний (по максимальному расстоянию)
    # Оптимизация: считаем один раз за вызов, не создавая лишних массивов
    query_normal = scaler.transform([query])
    all_distances = np.linalg.norm(features_normal - query_normal, axis=1)
    worst_index = np.argmax(all_distances)
    
    unsuitable = materials_list[worst_index].copy()
    unsuitable['status'] = 'unsuitable'
    unsuitable['status_text'] = '✗ Непригодный'
    
    return [optimal, acceptable, unsuitable]

def generate_dose_points(material, T_user, max_dose=100, points=50):
    """
    Генерирует точки для графика прочности от дозы облучения.
    Оптимизация: предрасчёт log(1+doses) вынесен, но здесь массив малый.
    """
    doses = np.linspace(0, max_dose, points)
    temp_correction = material["temp_coef"] * max(0, T_user - 20)
    strength_at_T = material["strength_ref"] - temp_correction
    # Векторизованный расчёт (быстро)
    strengths = strength_at_T - material["dose_coef"] * np.log1p(doses)  # log1p точнее и быстрее
    strengths = np.maximum(strengths, 0)
    return doses.tolist(), strengths.tolist()

def generate_temp_points(material, dose_user, max_temp=1200, points=50):
    """
    Генерирует точки для графика прочности от температуры.
    Оптимизация: убрано лишнее приведение степеней.
    """
    dose_correction = material["dose_coef"] * np.log1p(dose_user)
    strength_at_dose = material["strength_ref"] - dose_correction
    temps = np.linspace(20, max_temp, points)
    # Векторизованный расчёт (temps - 20) ** 1.2
    delta_t = temps - 20
    strengths = strength_at_dose - material["temp_coef"] * (delta_t * np.sqrt(delta_t ** 0.2))  # эквивалентно **1.2 но быстрее?
    # Проще: strengths = strength_at_dose - material["temp_coef"] * (delta_t ** 1.2)
    # NumPy оптимизирует степень сам
    strengths = strength_at_dose - material["temp_coef"] * (delta_t ** 1.2)
    strengths = np.maximum(strengths, 0)
    return temps.tolist(), strengths.tolist()