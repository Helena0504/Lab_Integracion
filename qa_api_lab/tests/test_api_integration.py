import sqlite3
import time
import pytest
import requests
from unittest.mock import MagicMock
import sys

BASE_URL = "https://fakestoreapi.com"


#Creacion de la base de datos en memoria para pruebas
@pytest.fixture
def db_connection():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE carrito (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            price REAL NOT NULL,
            cantidad INTEGER DEFAULT 1 CHECK(cantidad > 0),
            description TEXT,
            category TEXT,
            image TEXT
        )
    ''')

    conn.commit()
    yield conn
    conn.close()


#TESTEO DEL API. DONDE SE CONSULTA EL PRODUCTO
def test_consultar_productos():
    response = requests.get(f'{BASE_URL}/products', timeout=10)

    assert response.status_code == 200

    products = response.json()
    assert isinstance(products, list)
    assert len(products) > 0

    product = products[0]
    assert 'id' in product
    assert 'title' in product
    assert 'price' in product
    assert isinstance(product['price'], (int, float))


#----- 1 Insertar producto consultado en SQLite -----
def test_insertar_producto(db_connection):
    cursor = db_connection.cursor()

    response = requests.get(f'{BASE_URL}/products', timeout=10)
    assert response.status_code == 200

    products = response.json()
    assert isinstance(products, list)
    assert len(products) > 0

    product = products[0]

    cursor.execute("""
        INSERT INTO carrito (user_id, product_id, title, price, cantidad, description, category, image)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (1, product['id'], product['title'], product['price'], 1, product['description'], product['category'], product['image']))
    
    db_connection.commit()

    cursor.execute("SELECT COUNT(*) FROM carrito")
    total = cursor.fetchone()[0]

    assert total == 1

#----- 2 Validar total del carrito -----
#Creacion de la primera prueba de integracion, calcular el total del carrito
def test_validar_total_carrito(db_connection):
    cursor = db_connection.cursor()

    # Obtener productos reales desde la API
    response = requests.get(f'{BASE_URL}/products', timeout=10)
    assert response.status_code == 200

    products = response.json()[:3]
    cantidades = [2, 1, 3]
    user_id = 1

    productos_carrito = [
        (
            user_id,
            product['id'],
            product['title'],
            product['price'],
            cantidad
        )
        for product, cantidad in zip(products, cantidades)
    ]

    cursor.executemany("""
        INSERT INTO carrito (user_id, product_id, title, price, cantidad)
        VALUES (?, ?, ?, ?, ?)
    """, productos_carrito)

    db_connection.commit()

    total_esperado_productos = sum(cantidades)
    monto_esperado = sum(
        product['price'] * cantidad
        for product, cantidad in zip(products, cantidades)
    )

    # Calcular total de unidades y monto acumulado del carrito
    cursor.execute("""
        SELECT SUM(cantidad), SUM(price * cantidad)
        FROM carrito
        WHERE user_id = ?
    """, (user_id,))

    total_productos, monto_total = cursor.fetchone()

    assert total_productos == total_esperado_productos
    assert monto_total == pytest.approx(monto_esperado)

#----- 3 Validar cantidades -----
#Validacion de cantidades incorrectas en el carrito
def test_validar_cantidad_negativa(db_connection):
    cursor = db_connection.cursor()

    response = requests.get(f"{BASE_URL}/products", timeout=10)
    product = response.json()[0]

    cantidad = -1  # cantidad invalida

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO carrito (user_id, product_id, title, price, cantidad)
            VALUES (?, ?, ?, ?, ?)
        """, (1, product['id'], product['title'], product['price'], cantidad))

        db_connection.commit()


#----- 4 Ingresar porductos inexistentes -----
# Validar ingreso de un producto que no existe
def test_insertar_producto_inexistente(db_connection):
    cursor = db_connection.cursor()

    product_id_invalido = -10 #id de producto inválido

    response = requests.get(f"{BASE_URL}/products/{product_id_invalido}", timeout=10)
    assert response.status_code == 200 #valida la respuesta de la api
    try: #puede que no venga nada en data si es inválido
        data = response.json()
    except ValueError:
        data = {}

    # Valida si en realidad devolvió un producto, o en realidad el producto no existe
    assert data == {} or "id" not in data

    #Si el producto existe, se inserta en la bd
    if data and "id" in data:
        try:
            cursor.execute("""
                INSERT INTO carrito (user_id, product_id, title, price, cantidad, description, category, image)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (1, data["id"], data["title"], data["price"], 1, data["description"], data["category"], data["image"]))

            db_connection.commit()
        except sqlite3.IntegrityError as e:
            pytest.fail(f"Error inesperado al insertar datos válidos: {e}")

    cursor.execute("SELECT COUNT(*) FROM carrito")
    total = cursor.fetchone()[0]

    assert total == 0 # No debe insertarse en la bd si no existe


#----- 5 Medir tiempo de respuesta -----
#Medicion del tiempo de respuesta de la API
def test_tiempo_respuesta_api():
    tiempo_inicio = time.perf_counter()

    response = requests.get(f'{BASE_URL}/products', timeout=10)

    tiempo_fin = time.perf_counter()
    tiempo_respuesta = tiempo_fin - tiempo_inicio

    print(f"Tiempo de respuesta de la API: {tiempo_respuesta:.3f} segundos")

    assert response.status_code == 200
    assert tiempo_respuesta < 3

#Medir tiempo de respuesta (< 1000 ms)
def test_tiempo_respuesta_api_menos_1000ms():
    tiempo_inicio = time.perf_counter()

    response = requests.get(f'{BASE_URL}/products', timeout=10)

    tiempo_fin = time.perf_counter()
    tiempo_respuesta = tiempo_fin - tiempo_inicio

    tiempo_ms = tiempo_respuesta * 1000  # probar en milisegundos

    print(f"Tiempo de respuesta: {tiempo_ms:.2f} ms")

    assert response.status_code == 200
    assert tiempo_ms < 1000 


#----- 6 Autenticación simulada -----
# N/A, la api no tiene autenticación por token


#----- 7 Prueba de contrato estricta -----
#Validar que los tipos sean exactamente los del contrato
def test_contrato_estricto_productos(db_connection):
    cursor = db_connection.cursor()

    response = requests.get(f"{BASE_URL}/products", timeout=10)
    assert response.status_code == 200 #valida respuesta de api
    product = response.json()[0]

    #Valida que los tipos cumplan con el contrato
    assert isinstance(product["id"], int)
    assert isinstance(product["title"], str)
    assert isinstance(product["price"], (int, float))
    assert isinstance(product["category"], str)
    assert isinstance(product["image"], str)

    # Si cumple con el contrato, entra a bd
    try:
        cursor.execute("""
            INSERT INTO carrito (user_id, product_id, title, price, cantidad, description, category, image)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (1, product["id"], product["title"], product["price"], 1, 
            product["description"], product["category"], product["image"]))
        db_connection.commit()
    except sqlite3.IntegrityError as e:
        pytest.fail(f"Error inesperado al insertar datos válidos: {e}")

    cursor.execute("SELECT COUNT(*) FROM carrito")
    total = cursor.fetchone()[0]

    assert total == 1

#----- 8 Idempotencia -----
#Prueba de idempotencia
def test_idempotencia_insercion_carrito(db_connection):
    cursor = db_connection.cursor()

    response = requests.get(f"{BASE_URL}/products", timeout=10)
    product = response.json()[0]

    user_id = 1
    product_id = product['id']
    title = product['title']
    price = product['price']
    cantidad = 1

    # Primera inserción
    cursor.execute("""
        INSERT INTO carrito (user_id, product_id, title, price, cantidad)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, product_id, title, price, cantidad))
    db_connection.commit()

    # Segunda inserción del mismo producto para el mismo usuario
    cursor.execute("""
        INSERT INTO carrito (user_id, product_id, title, price, cantidad)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, product_id, title, price, cantidad))
    db_connection.commit()

    cursor.execute("""
        SELECT COUNT(*)
        FROM carrito
        WHERE user_id = ? AND product_id = ?
    """, (user_id, product["id"]))

    total_registros = cursor.fetchone()[0]

    assert total_registros == 2

#----- 9 Manejo de errores -----
#Forzar un body incompleto
def test_body_incompleto(db_connection):
    cursor = db_connection.cursor()

    #body incompleto
    body_incompleto = {
        "id": 1,
        "title": "string"
    }

    response = requests.post(f"{BASE_URL}/products",json=body_incompleto, timeout=10)
    data = response.json()

    assert data is not None

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO carrito (user_id, product_id, title, price, cantidad, description, category, image)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (1, data.get("id"), data.get("title"), data.get("price"), 1,
            data.get("description"), data.get("category"), data.get("image")))

        db_connection.commit()

    cursor.execute("SELECT COUNT(*) FROM carrito")
    total = cursor.fetchone()[0]

    assert total == 0 #verificar que no ingresó

#----- 10 Prueba de integración parcial -----
#Prueba de integracion parcial
def test_integracion_parcial_api_ok_db_falla(db_connection):
    cursor = db_connection.cursor()

    # 1. La API responde correctamente
    response = requests.get(f"{BASE_URL}/products", timeout=10)
    assert response.status_code == 200

    product = response.json()[0]
    assert "id" in product
    assert "title" in product
    assert "price" in product

    # 2. Simular fallo de base de datos:
    # Se intenta insertar sin title, pero title es NOT NULL
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO carrito (
                user_id, product_id, price, cantidad
            )
            VALUES (?, ?, ?, ?)
        """, (
            1,
            product["id"],
            product["price"],
            1
        ))

        db_connection.commit()

#----- 11 Mock opcional -----
def test_mock_api_caida(db_connection, monkeypatch):
    cursor = db_connection.cursor()

    fake_requests = MagicMock() #se crea un requests falso y se simula que la API falla
    fake_requests.get.side_effect = Exception("API falla")

    monkeypatch.setitem(sys.modules, "requests", fake_requests) #cuando se intente llamar requests, se llamará al falso

    import requests #se importa el falso

    with pytest.raises(Exception):
        requests.get("https://fakestoreapi.com/products") #se simula la falla

    cursor.execute("SELECT COUNT(*) FROM carrito")
    total = cursor.fetchone()[0]

    assert total == 0

