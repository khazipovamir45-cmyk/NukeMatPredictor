import sqlite3
import numpy as np
import joblib
from sklearn.preprocessing import StandardScaler# это нужно для нормализации характеристик, чтобы характеристики влияли на подбор примерно одинаково
# Далее устанавливаю связь с базой данных
from database import get_all_materials
materials = get_all_materials()
features = []# 5 чисел, 5 признаков
materials_list = []
print(materials)
print(materials[0].keys())
for material in materials:
    row = [material["temperature"], material["min_required_strength"], material["irradiation_dose"], material["thermal_conductivity"], material["heat_capacity"], ]
    features.append(row)
    material_info = {
        'name': material['name'],
        'irradiation_dose': material['irradiation_dose'],
        'corrosion_rate': material['corrosion_rate'],
        'temp_coef': material['temp_coef'],
        'dose_coef': material['dose_coef'],
        'strength_ref': None # прочность материала при комнатной темпаратуре и нулевой dpa, считаю  сейчас, а пользоваться буду в model.py в формулах зависимостей
    }# это список для работы model.py, то есть характериситики для таблицы из трех материалов 
    materials_list.append(material_info)
scaler  = StandardScaler()
feature_normal = scaler.fit_transform(features)# нормализация, то есть прииведение к единому масштабу
joblib.dump(scaler, 'scaler.pkl')# изменяю объект scaler и сохраняю его в новый файл, причем в нем будут стандартные отклонения и средние значения по столбцам, с помощью которых как раз и просиходит нормализация
np.save('features.npy', feature_normal)# сохраняю в формате npy потому что он намного быстреее работает, чем txt файл к пример
for i, material in enumerate(materials):
    strength_ref = material["min_required_strength"] + material["temp_coef"] * max(0, material['temperature'] - 20) + material["dose_coef"] * material["irradiation_dose"]
    materials_list[i]["strength_ref"] = strength_ref
joblib.dump(materials_list, "materials_list.pkl")