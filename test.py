import requests

url = "http://localhost:8000/api/recipes/"  # Полный адрес эндпоинта
response = requests.get(url)  # Делаем GET-запрос
response_on_python = response.json()
for recipe in response_on_python:
    if recipe["title"] == "Брускетта":
        print(recipe["recipe"])
# Поскольку данные пришли в формате json, переведем их в python
# response_on_python = response.json()

# Запишем полученные данные в файл capitals.txt
# with open("recipes.txt", "w") as file:
#    for recipe in response_on_python:
#        file.write(
#            f"The population of {recipe['title']} is "
#            f"{recipe['ingredients']}, "
#            f"{recipe['recipe']}, \n"
#       )
