import joblib
import numpy as np
import os

scaler = None
materials_list = None
features_normal = None


def load_knn_data():
    """Загружает данные модели при старте сервера (один раз)."""
    global scaler, materials_list, features_normal
    base_dir = os.path.dirname(os.path.abspath(__file__))

    scaler = joblib.load(os.path.join(base_dir, "scaler.pkl"))
    materials_list = joblib.load(os.path.join(base_dir, "materials_list.pkl"))
    features_normal = np.load(os.path.join(base_dir, "features.npy"))


def rank_materials(temp, dose, strength, therm_cond, heat_cap):
    """
    Возвращает 3 материала: оптимальный, допустимый, непригодный.
    Один scaler.transform, один проход по расстояниям.
    """
    query = [temp, strength, dose, therm_cond, heat_cap]
    query_normal = scaler.transform([query])
    distances = np.linalg.norm(features_normal - query_normal, axis=1)

    # Топ-2 ближайших — argpartition не сортирует весь массив
    k = 2
    nearest = np.argpartition(distances, k)[:k]
    nearest = nearest[np.argsort(distances[nearest])]
    worst_index = int(np.argmax(distances))

    optimal = materials_list[nearest[0]].copy()
    optimal['status'] = 'optimal'
    optimal['status_text'] = '★ Оптимальный'

    acceptable = materials_list[nearest[1]].copy()
    acceptable['status'] = 'acceptable'
    acceptable['status_text'] = '✓ Допустимый'

    unsuitable = materials_list[worst_index].copy()
    unsuitable['status'] = 'unsuitable'
    unsuitable['status_text'] = '✗ Непригодный'

    return [optimal, acceptable, unsuitable]


def generate_dose_points(material, T_user, max_dose=100, points=50):
    """График прочности от дозы облучения."""
    doses = np.linspace(0, max_dose, points)
    temp_correction = material["temp_coef"] * max(0, T_user - 20)
    strength_at_T = material["strength_ref"] - temp_correction
    strengths = strength_at_T - material["dose_coef"] * np.log1p(doses)
    strengths = np.maximum(strengths, 0)
    return doses.tolist(), strengths.tolist()


def generate_temp_points(material, dose_user, max_temp=1200, points=50):
    """График прочности от температуры."""
    dose_correction = material["dose_coef"] * np.log1p(dose_user)
    strength_at_dose = material["strength_ref"] - dose_correction
    temps = np.linspace(20, max_temp, points)
    delta_t = temps - 20
    strengths = strength_at_dose - material["temp_coef"] * (delta_t ** 1.2)
    strengths = np.maximum(strengths, 0)
    return temps.tolist(), strengths.tolist()


def compute_full_result(temp, dose, strength, therm_cond, heat_cap):
    """
    Считает материалы и оба графика одним вызовом —
    нужно, чтобы кэш в app.py возвращал всё разом, без повторного построения графиков.
    Возвращает (materials, (dose_x, dose_y), (temp_x, temp_y)).
    """
    materials = rank_materials(temp, dose, strength, therm_cond, heat_cap)
    best = materials[0]
    dose_points = generate_dose_points(best, temp)
    temp_points = generate_temp_points(best, dose)
    return materials, dose_points, temp_points
