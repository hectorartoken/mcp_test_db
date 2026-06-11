import os # variables de entorno
from typing import List, Dict, Any, Optional # tipos de datos
from datetime import datetime # manejo de fechas
import psycopg2 # conexión a PostgreSQL
from psycopg2.extras import RealDictCursor # cursor para obtener resultados como diccionarios
from fastmcp import FastMCP # clase para manejar la lógica de negocio

app = FastMCP("company-db-sever")

def get_db_connection():

    conn = psycopg2.connect(
        host = os.environ.get("DB_HOST"),
        port = int(os.environ.get("DB_PORT")),
        user = os.environ.get("DB_USER"),
        password = os.environ.get("DB_PASSWORD"),
        dbname = os.environ.get("DB_DATABASE"),
        cursor_factory = RealDictCursor
    )
    return conn

@app.tool
def list_employees(limit: int = 5) -> List[Dict[str, Any]]:
    """Lista los empleados de la empresa con un límite opcional."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT id, name, position, department, salary, hire_date
                       FROM employees
                       ORDER BY id
                       LIMIT %s
                       """, (limit,))
        rows = cursor.fetchall()
        employees = []
        for row in rows:
            employee = {
                "id": row["id"],
                "name": row["name"],
                "position": row["position"],
                "department": row["department"],
                "salary": float(row["salary"]),
                "hire_date": str(row["hire_date"])
            }
            employees.append(employee)
        cursor.close()
        conn.close()
        return employees
    except Exception as e:
        return {"error": str(e)}

@app.tool
def add_employee(name: str, position: str, department: str, salary: float, hire_date: Optional[str] = None) -> Dict[str, Any]:
    """Agrega un nuevo empleado a la base de datos."""
    try:
        if not name.strip():
            return {"error": "El nombre del empleado no puede estar vacío."}
        
        if salary <= 0:
            return {"error": "El salario debe ser un número positivo."}
        
        if not hire_date:
            hire_date = datetime.now().strftime("%Y-%m-%d")
        
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
                       INSERT INTO employees (name, position, department, salary, hire_date)
                       VALUES (%s, %s, %s, %s, %s)
                       RETURNING id, name, position, department, salary, hire_date
                       """, (name.strip(), position.strip(), department.strip(), salary, hire_date))
        new_employee = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        return {
            "status": True,
            "employee": {
                "id": new_employee["id"],
                "name": new_employee["name"],
                "position": new_employee["position"],
                "department": new_employee["department"],
                "salary": float(new_employee["salary"]),
                "hire_date": str(new_employee["hire_date"])
            }
        }
    except Exception as e:
        return {"error": f"Error al agregar empleado: {str(e)}"}

if __name__ == "__main__":
    app.run(transport="sse", host="0.0.0.0", port=3000)
    