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

## Ejecutable

La aplicación puede empaquetarse en un único archivo ejecutable usando *PyInstaller*, lo que permite correrla sin necesidad de instalar Python, uv ni las dependencias del proyecto.

### Generar el ejecutable

Con las dependencias de desarrollo instaladas (`uv sync`), desde la raíz del repositorio ejecutar:

```bash
uv run pyinstaller --onefile --name is-i-project --paths src \
    --add-data "src/is_i_project/templates:is_i_project/templates" \
    --add-data "src/is_i_project/static:is_i_project/static" \
    src/is_i_project/__main__.py
```

El ejecutable se genera en la carpeta **dist/**. *PyInstaller* genera el ejecutable para el sistema operativo en el que se corre el comando, por lo que en Windows se obtiene `dist/is-i-project.exe`.

### Ejecutar la aplicación

```bash
./dist/is-i-project
```

Al iniciarse se crea automáticamente la base de datos SQLite (`dev.db`) junto al ejecutable, si es que no existe, y se levanta el servidor web en [http://127.0.0.1:5000](http://127.0.0.1:5000). El puerto puede cambiarse con la variable de entorno `PORT`.
