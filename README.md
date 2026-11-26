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

La aplicación puede empaquetarse en un único archivo ejecutable usando *PyInstaller*, lo que permite correrla en **Linux** y **Windows** sin necesidad de instalar Python, uv ni las dependencias del proyecto.

Además, el repositorio cuenta con un flujo de *GitHub Actions* que compila automáticamente ambos ejecutables (`is-i-project` para Linux e `is-i-project.exe` para Windows) y los publica como artefactos descargables (`is-i-project-linux` e `is-i-project-windows`) en la pestaña **Actions**.

### Generar el ejecutable

Con las dependencias de desarrollo instaladas (`uv sync`), desde la raíz del repositorio ejecutar:

En **Linux**:

```bash
uv run pyinstaller --onefile --name is-i-project --paths src \
    --add-data "src/is_i_project/templates:is_i_project/templates" \
    --add-data "src/is_i_project/static:is_i_project/static" \
    src/is_i_project/__main__.py
```

En **Windows** (*PowerShell*):

```powershell
uv run pyinstaller --onefile --name is-i-project --paths src `
    --add-data "src/is_i_project/templates:is_i_project/templates" `
    --add-data "src/is_i_project/static:is_i_project/static" `
    src/is_i_project/__main__.py
```

El ejecutable se genera en la carpeta **dist/** (`dist/is-i-project` en Linux y `dist/is-i-project.exe` en Windows).

### Ejecutar la aplicación

En **Linux**:

```bash
./dist/is-i-project
```

En **Windows**:

```powershell
.\dist\is-i-project.exe
```

Al iniciarse se crea automáticamente la base de datos SQLite (`dev.db`) junto al ejecutable, si es que no existe, y se levanta el servidor web en [http://127.0.0.1:5000](http://127.0.0.1:5000). El puerto puede cambiarse con la variable de entorno `PORT`.
