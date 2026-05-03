import sqlite3
import time
import pytest
import requests

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


#Medicion del tiempo de respuesta de la API
def test_tiempo_respuesta_api():
    tiempo_inicio = time.perf_counter()

    response = requests.get(f'{BASE_URL}/products', timeout=10)

    tiempo_fin = time.perf_counter()
    tiempo_respuesta = tiempo_fin - tiempo_inicio

    print(f"Tiempo de respuesta de la API: {tiempo_respuesta:.3f} segundos")

    assert response.status_code == 200
    assert tiempo_respuesta < 3


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
