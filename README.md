# Ingeniería de software I - Plataforma de QA

Integrantes:
- Juan Manuel Antuña
- Román Maldonado
- Tomás Ezequiel Miranda Gottardi
- Valentín Tello
- Hilario Yáñez Bertola

## Primera entrega: Modelado con patrones de diseño

El diagrama de clases que usamos para modelar el proyecto se encuentra en [AGREGAR LINK](https://media.licdn.com/dms/image/v2/D5603AQHig3pgzff-Tw/profile-displayphoto-shrink_800_800/B56ZOOhHu6GkAg-/0/1733262868135?e=1794441600&v=beta&t=Dbn5jyrggJcjp8VcLPvUSIhwhW6m8oN9BNpcAsug_s8).

Para gestionar los autores y abstraerlo decidimos utilizar el patrón *factory method*. Esto nos permite disponer de una clase abstracta **Autor** la cual define el comportamiento y define la interfaz que será usada por el resto de componentes del sistema, junto con una fábrica que permite generar autores a necesidad. Además, la entidad concreta **AutorIA** implementa un patrón *Strategy*, modelando así la posibilidad de usar distintos proveedores de IA sin acumular ni acoplar lógica innecesaria.
