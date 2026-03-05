import flet as ft
import csv
import os
from datetime import datetime

RUTA_DATOS = os.getenv("FLET_APP_DATA", os.getcwd())
ARCHIVO_INV = os.path.join(RUTA_DATOS, "datos_almacen.csv")
ARCHIVO_HIST = os.path.join(RUTA_DATOS, "historial_almacen.csv")

class MiAlmacen:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Mi Almacén"
        self.page.theme_mode = "dark"
        self.page.scroll = "adaptive"
        
        self.txt_codigo = ft.TextField(label="ID / Código", width=150)
        self.txt_cantidad = ft.TextField(label="Cant.", width=80, value="1", keyboard_type="number")
        self.txt_nombre = ft.TextField(label="Nombre del Producto", expand=True)
        self.txt_buscar = ft.TextField(label="🔍 Buscar producto...", on_change=self.filtrar_lista)
        self.lbl_total_piezas = ft.Text("Total: 0", size=22, weight="bold", color="blue200")
        self.contenedor_vistas = ft.Column()

        self.page.add(
            ft.Row([
                ft.Icon(ft.Icons.STORE, color="blue400", size=30),
                ft.Text("MI ALMACÉN", size=30, weight="bold"),
            ], alignment="center"),
            ft.Row([
                ft.ElevatedButton("INVENTARIO", icon=ft.Icons.LIST_ALT, on_click=lambda _: self.mostrar_inventario(), expand=True),
                ft.ElevatedButton("HISTORIAL", icon=ft.Icons.HISTORY, on_click=lambda _: self.mostrar_historial(), expand=True),
            ]),
            ft.Divider(),
            self.contenedor_vistas
        )
        self.mostrar_inventario()

    def limpiar_campos(self, e=None):
        self.txt_codigo.value = ""
        self.txt_nombre.value = ""
        self.txt_cantidad.value = "1"
        self.page.update()

    def registrar_movimiento(self, cod, nombre, tipo, cant):
        fecha = datetime.now().strftime("%d/%m %H:%M")
        try:
            with open(ARCHIVO_HIST, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([fecha, cod, nombre, tipo, cant])
        except: pass

    def borrar_producto(self, codigo):
        inventario = []
        if os.path.exists(ARCHIVO_INV):
            with open(ARCHIVO_INV, mode='r', encoding='utf-8') as f:
                for r in csv.DictReader(f):
                    if r['Codigo'] != codigo: inventario.append(r)
            with open(ARCHIVO_INV, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Codigo', 'Nombre', 'Cantidad'])
                writer.writeheader()
                writer.writerows(inventario)
            self.mostrar_inventario()

    def actualizar_stock(self, operacion):
        cod = self.txt_codigo.value.upper().strip()
        nom = self.txt_nombre.value.strip()
        if not cod: return
        try:
            cant_input = int(self.txt_cantidad.value)
            inventario = {}
            if os.path.exists(ARCHIVO_INV):
                with open(ARCHIVO_INV, mode='r', encoding='utf-8') as f:
                    for r in csv.DictReader(f):
                        inventario[r['Codigo']] = {'nombre': r['Nombre'], 'cantidad': int(r['Cantidad'])}
            
            if operacion == "sumar":
                if cod in inventario: inventario[cod]['cantidad'] += cant_input
                else: inventario[cod] = {'nombre': nom or "Nuevo", 'cantidad': cant_input}
                self.registrar_movimiento(cod, inventario[cod]['nombre'], "ENTRADA", cant_input)
            elif operacion == "restar" and cod in inventario:
                if inventario[cod]['cantidad'] >= cant_input:
                    inventario[cod]['cantidad'] -= cant_input
                    self.registrar_movimiento(cod, inventario[cod]['nombre'], "SALIDA", cant_input)
            
            with open(ARCHIVO_INV, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Codigo', 'Nombre', 'Cantidad'])
                writer.writeheader()
                for k, v in inventario.items():
                    writer.writerow({'Codigo': k, 'Nombre': v['nombre'], 'Cantidad': v['cantidad']})
            
            self.limpiar_campos()
            self.mostrar_inventario()
        except: pass

    def mostrar_inventario(self, filtro=""):
        self.contenedor_vistas.controls.clear()
        self.contenedor_vistas.controls.append(ft.Column([
            ft.Row([self.txt_codigo, self.txt_cantidad]),
            self.txt_nombre,
            ft.Row([
                ft.ElevatedButton("SUMAR", bgcolor="green", color="white", icon=ft.Icons.ADD, on_click=lambda _: self.actualizar_stock("sumar"), expand=True),
                ft.ElevatedButton("RESTAR", bgcolor="red", color="white", icon=ft.Icons.REMOVE, on_click=lambda _: self.actualizar_stock("restar"), expand=True),
            ]),
            ft.TextButton("Limpiar campos", icon=ft.Icons.REFRESH, on_click=self.limpiar_campos)
        ]))
        self.contenedor_vistas.controls.append(ft.Divider())
        self.contenedor_vistas.controls.append(self.txt_buscar)
        
        lista_items = ft.Column(spacing=10)
        suma_total = 0
        if os.path.exists(ARCHIVO_INV):
            with open(ARCHIVO_INV, mode='r', encoding='utf-8') as f:
                for r in csv.DictReader(f):
                    cant = int(r['Cantidad'])
                    suma_total += cant
                    if filtro in r['Nombre'].lower() or filtro in r['Codigo'].lower():
                        color_a = "red900" if cant == 0 else "orange900" if cant <= 5 else "#2a2a2a"
                        lista_items.controls.append(
                            ft.Container(
                                content=ft.Row([
                                    ft.Column([ft.Text(r['Nombre'], weight="bold"), ft.Text(f"ID: {r['Codigo']} | Stock: {cant}")], expand=True),
                                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="white", on_click=lambda e, c=r['Codigo']: self.borrar_producto(c))
                                ]),
                                padding=10, bgcolor=color_a, border_radius=10,
                                on_click=lambda e, r=r: self.cargar(r['Codigo'], r['Nombre'])
                            )
                        )
        self.lbl_total_piezas.value = f"Total de piezas: {suma_total}"
        self.contenedor_vistas.controls.append(self.lbl_total_piezas)
        self.contenedor_vistas.controls.append(lista_items)
        self.page.update()

    def filtrar_lista(self, e): self.mostrar_inventario(filtro=self.txt_buscar.value.lower())
    def cargar(self, c, n): 
        self.txt_codigo.value = c
        self.txt_nombre.value = n
        self.page.update()

    def mostrar_historial(self):
        self.contenedor_vistas.controls.clear()
        self.contenedor_vistas.controls.append(ft.Row([ft.Icon(ft.Icons.HISTORY), ft.Text("HISTORIAL RECIENTE", size=20, weight="bold")]))
        if os.path.exists(ARCHIVO_HIST):
            with open(ARCHIVO_HIST, mode='r', encoding='utf-8') as f:
                lineas = list(csv.reader(f))
                for r in reversed(lineas[-25:]):
                    icon_h = ft.Icons.ARROW_UPWARD if r[3] == "ENTRADA" else ft.Icons.ARROW_DOWNWARD
                    color_h = "green" if r[3] == "ENTRADA" else "red"
                    self.contenedor_vistas.controls.append(
                        ft.ListTile(leading=ft.Icon(icon_h, color=color_h), title=ft.Text(f"{r[2]} ({r[4]})"), subtitle=ft.Text(f"{r[0]} - {r[3]}"))
                    )
        self.page.update()

def main(page: ft.Page):
    MiAlmacen(page)

if __name__ == "__main__":
    ft.app(target=main)

