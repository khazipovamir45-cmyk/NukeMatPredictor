import joblib
import math
import numpy as np

scaler = None
materials_list = None
features_normal = None


def load_knn_data():
    global scaler, materials_list, features_normal
    scaler = joblib.load(
        "scaler.pkl")  # использую joblib, потому что в prepare  я превращал питоновский объект в файл с помощью этой библиотеки
    materials_list = joblib.load("materials_list.pkl")
    features_normal = np.load("features.npy")


def find_nearest(query, k=5):
    query_normal = scaler.transform([query])
    dist = np.linalg.norm(features_normal - query_normal,
                          axis=1)  # axis=1 это обозначакет что мы идем по стодбцам матрицы, а axis = 0 обозначает что мы идем по строкам матрицы 
    indexes = np.argsort(dist)[
              :k]  # я создаю массив из индексов тех материалов из 5 которые ближе всего к заданному и здесь же как раз и происходит сортировка по возрастанию
    nearest_distances = dist[indexes]  # 4.Берём сами расстояния для этих индексов от заданной до ближайших 5 материалов
    return indexes, nearest_distances


def rank_materials(temp, dose, strength, therm_cond, heat_cap):
    query = [temp, strength, dose, therm_cond, heat_cap]

    indices, distances = find_nearest(query, k=5)

    optimal = materials_list[indices[0]].copy()# создаю копию для того чтобы потом словарь с подходящим материалом изменять(добавлять) статус и текст статуса который будет отображаться на сайте
    optimal['status'] = 'optimal'
    optimal['status_text'] = '★ Оптимальный'

    acceptable = materials_list[indices[1]].copy()
    acceptable['status'] = 'acceptable'
    acceptable['status_text'] = '✓ Допустимый'

    query_normal = scaler.transform([query])
    all_distances = np.linalg.norm(features_normal - query_normal, axis=1)
    worst_index = np.argmax(all_distances)

    unsuitable = materials_list[worst_index].copy()
    unsuitable['status'] = 'unsuitable'
    unsuitable['status_text'] = '✗ Непригодный'

    return [optimal, acceptable, unsuitable]


def generate_dose_points(material, T_user, max_dose=100, points=50):
    doses = np.linspace(0, max_dose,
                        points)  # то есть здесь от 0 до 10 будет 50 точек с координатами равномерно распределенным по y
    temp_correction = material["temp_coef"] * max(0, T_user - 20)
    strength_at_T = material["strength_ref"] - temp_correction
    strengths = strength_at_T - material["dose_coef"] * np.log(1 + doses)
    strengths = np.maximum(strengths, 0)
    return doses.tolist(), strengths.tolist()


def generate_temp_points(material, dose_user, max_temp=1200, points=50):
    dose_correction = material["dose_coef"] * np.log(1 + dose_user)
    strength_at_dose = material["strength_ref"] - dose_correction
    temps = np.linspace(20, max_temp, points)
    strengths = strength_at_dose - material["temp_coef"] * (temps - 20) ** 1.2
    strengths = np.maximum(strengths, 0)
    return temps.tolist(), strengths.tolist()