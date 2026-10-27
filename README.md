# Ingeniería de software I - Plataforma de QA

Integrantes:
- Juan Manuel Antuña
- Román Maldonado
- Tomás Ezequiel Miranda Gottardi
- Valentín Tello
- Hilario Yáñez Bertola

## Primera entrega: Modelado con patrones de diseño

El diagrama de clases que usamos para modelar el proyecto se encuentra en [docs](docs/class-diagram.png).

Para gestionar los autores y abstraerlo decidimos utilizar el patrón *factory method*. Esto nos permite disponer de una clase abstracta **Autor** la cual define el comportamiento y define la interfaz que será usada por el resto de componentes del sistema, junto con una fábrica que permite generar autores a necesidad. Además, la entidad concreta **AutorIA** implementa un patrón *Strategy*, modelando así la posibilidad de usar distintos proveedores de IA sin acumular ni acoplar lógica innecesaria.
