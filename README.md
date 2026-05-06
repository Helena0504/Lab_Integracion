# Laboratorio de Integracion API

Este laboratorio valida integraciones usando dos enfoques:

- Pruebas automatizadas con `pytest` en Python.
- Pruebas manuales y automatizadas con Postman y Collection Runner.

La API utilizada es:

```text
https://fakestoreapi.com
```
## Entregables
Encontrará los entregables ubicados en los siguientes documentos:
- En el pdf "Laboratorio_Integracion.pdf" encontrará:
    - La matriz de casos de prueba.
    - Las capturas de ejecución de Postman.
    - La evidencia de ejecución de Pytest.
    - Reporte final con métricas, hallazgos, defectos y conclusiones.
- Dentro de la carpeta "qa_api_lab" encontrará
    - Los tests realizados con pytest
    - requirements
    - Las instrucciones de su ejecución se encuentran más adelante
- De manera separada encontrará dos JSON, correspondientes a la collection y el environment de postman



## Requisitos

Antes de ejecutar el laboratorio, instalar:

- Python 3.10 o superior.
- Postman.
- Conexion a internet.
- Dependencias de Python: `pytest`, `MagicMock` y `requests`.

## Estructura del proyecto

```text
qa_api_lab/
  README.md
  requirements.txt
  tests/
    test_api_integration.py
```

El archivo principal de pruebas automatizadas es:

```text
qa_api_lab/tests/test_api_integration.py
```

## Instalacion de dependencias

Abrir una terminal PowerShell en la carpeta raiz del proyecto:

```powershell
cd "c:\Users\caray\OneDrive - Estudiantes ITCR\Documentos\TEC\S1-2026\Aseguramiento\TAREAS\LAB 9\Lab_Integracion"
```

Instalar las dependencias desde `requirements.txt`:

```powershell
pip install -r .\qa_api_lab\requirements.txt
```

Tambien se pueden instalar manualmente:

```powershell
pip install pytest requests
```

## Ejecucion de pruebas con pytest

Para ejecutar todas las pruebas del laboratorio:

```powershell
pytest .\qa_api_lab\tests\test_api_integration.py
```

Para ejecutar las pruebas con mas detalle:

```powershell
pytest .\qa_api_lab\tests\test_api_integration.py -v
```

Para ejecutar solo la prueba que valida el total del carrito:

```powershell
pytest .\qa_api_lab\tests\test_api_integration.py::test_validar_total_carrito
```

## Que validan las pruebas automatizadas

Las pruebas incluidas validan:

- Que la API de productos responda correctamente.
- Que la respuesta tenga una lista de productos.
- Que los productos tengan campos esperados como `id`, `title` y `price`.
- Que se puedan insertar productos en una base SQLite en memoria.
- Que el carrito calcule correctamente:
  - Total de unidades con `SUM(cantidad)`.
  - Monto total con `SUM(price * cantidad)`.
- Que las cantidades sean mayores que cero.
- Que se pueda verificar el comportamiento al insertar productos repetidos.
- Que se controle un fallo parcial cuando la API responde bien pero la base de datos rechaza datos invalidos.

## Pruebas en Postman

La coleccion de Postman usada en este laboratorio se llama:

```text
API - Carrito
```

Enlace de la coleccion:

```text
https://carolarayaconejo.postman.co/workspace/Carol-Araya-Conejo's-Workspace~d09971d2-3814-44c1-8d2a-a2d85cc1ca73/collection/44963113-79f59649-67cf-4f4c-b1db-6e992ceae9da?action=share&creator=44963113&active-environment=44963113-46e24b46-f7cb-43b3-a97a-048951cc179e
```

### Abrir la coleccion

1. Abrir Postman.
2. Iniciar sesion con la cuenta correspondiente.
3. Abrir el enlace de la coleccion compartida.
4. Verificar que se muestre la coleccion `API - Carrito`.
5. Seleccionar el ambiente `QA_API_LAB`, si esta disponible.

### Estructura de la coleccion

La coleccion esta organizada en las siguientes carpetas:

- `Catalogo`: pruebas relacionadas con productos.
- `Carrito`: pruebas relacionadas con creacion y consulta de carritos.
- `Total`: prueba para calcular o validar el total del carrito.
- `Checkout`: carpeta reservada para flujo de compra.
- `Errores`: pruebas negativas o casos invalidos.

### Solicitudes principales

En la carpeta `Catalogo`:

- `Consultar Productos`: obtiene la lista de productos.
- `Anadir Producto`: prueba el envio de un producto.
- `Consultar un producto por id`: obtiene un producto especifico.

En la carpeta `Carrito`:

- `Anadir carrito`: prueba la creacion de un carrito.
- `Obtener un carrito`: obtiene la informacion de un carrito existente.

En la carpeta `Total`:

- `Calcular Total Carrito`: valida el total de productos o monto del carrito.

En la carpeta `Errores`:

- `Anadir datos invalidos al carrito`.
- `Anadir producto invalido al carrito`.
- `Consultar producto inexistente`.
- `Enviar body incompleto a carts`.
- `Enviar body incompleto a products`.


Nota: los endpoints de carritos de Fake Store API devuelven `productId` pero no `quantity`. Si se necesita validar el monto total, se debe consultar tambien el detalle de cada producto para obtener su `price`, o usar valores esperados definidos en la coleccion.

## Ejecutar con Collection Runner

Para ejecutar la coleccion completa en Postman:

1. Abrir Postman.
2. Ir a `Collections`.
3. Seleccionar la coleccion `API - Carrito`.
4. Dar clic en `Run`.
5. Verificar que esten seleccionadas las solicitudes que se desean ejecutar.
6. Configurar el numero de iteraciones. Para este laboratorio puede usarse `3`.
7. Dar clic en `Run API - Carrito`.
8. Revisar que todas las pruebas aparezcan como `Passed`.


## Resultado esperado

Al finalizar el laboratorio:

- Las pruebas de `pytest` deben finalizar con estado `passed`.
- Las pruebas de Postman deben mostrarse como `Passed`.
- El Collection Runner debe mostrar todas las iteraciones exitosas.

## Problemas comunes

Si falla la prueba por conexion:

```text
requests.exceptions.ProxyError
requests.exceptions.ConnectionError
```

Verificar que exista conexion a internet y que el proxy o firewall permita acceder a:

```text
https://fakestoreapi.com
```

Si `pytest` no se reconoce como comando:

```powershell
pip install pytest
```

Si `requests` no esta instalado:

```powershell
pip install requests
```
