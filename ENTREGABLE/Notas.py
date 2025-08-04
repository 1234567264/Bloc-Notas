import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime, date
from tkcalendar import Calendar
import sqlite3
import os

# ---------- BASE DE DATOS ----------
conn = sqlite3.connect('Mis_Tareas.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS tareas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT,
        descripcion TEXT,
        prioridad TEXT,
        fecha_limite TEXT,
        fecha_creacion TEXT,
        historial_actualizacion TEXT
    )
''')
conn.commit()

# ---------- CLASE DE APLICACIÓN ----------
class Aplicacion:
    def __init__(self, root):
        self.bg_color = "#f4f4f9"
        self.fg_color = "#333"
        self.highlight = "#3e64ff"
        self.root = root
        self.root.title("🧠 Gestor de Tareas Empresarial")
        self.root.configure(bg=self.bg_color)
        self.root.geometry("850x500")
        self.root.resizable(False, False)

        # Tabla con Scrollbar
        self.lista_tareas = ttk.Treeview(root, columns=("ID", "Titulo", "Prioridad", "Fecha limite"), show='headings', height=10)
        self.lista_tareas.heading("ID", text="ID")
        self.lista_tareas.heading("Titulo", text="Título")
        self.lista_tareas.heading("Prioridad", text="Prioridad")
        self.lista_tareas.heading("Fecha limite", text="Fecha límite")
        self.lista_tareas.pack(pady=20, padx=10)

        scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.lista_tareas.yview)
        scrollbar.pack(side="right", fill="y")
        self.lista_tareas.configure(yscrollcommand=scrollbar.set)

        # Botones
        btn_frame = tk.Frame(root, bg=self.bg_color)
        btn_frame.pack()

        tk.Button(btn_frame, text="➕ Agregar", width=15, bg=self.highlight, fg='white', command=self.agregar_tarea).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="✏️ Actualizar", width=15, bg=self.highlight, fg='white', command=self.actualizar_tarea).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ Eliminar", width=15, bg=self.highlight, fg='white', command=self.eliminar_tarea).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="📖 Ver Contenido", width=15, bg=self.highlight, fg='white', command=self.ver_detalles).pack(side=tk.LEFT, padx=5)

        self.actualizar_lista()

    def obtener_prioridad(self, ventana):
        prioridad_var = tk.StringVar(value="Media")
        tk.Label(ventana, text="Prioridad:").pack()
        frame = tk.Frame(ventana)
        frame.pack()
        for p in ["Alta", "Media", "Baja"]:
            tk.Radiobutton(frame, text=p, variable=prioridad_var, value=p).pack(side=tk.LEFT, padx=5)
        return prioridad_var

    def obtener_fecha_calendario(self, ventana):
        fecha_var = tk.StringVar()

        def abrir_calendario():
            top = tk.Toplevel(ventana)
            top.title("Seleccionar Fecha")
            top.configure(bg="#fafafa")
            cal = Calendar(top, selectmode='day', date_pattern='yyyy-mm-dd')
            cal.pack(padx=10, pady=10)

            def confirmar():
                fecha = cal.get_date()
                fecha_var.set(str(fecha))
                top.destroy()

            ttk.Button(top, text="OK", command=confirmar).pack(pady=5)

        fecha_frame = tk.Frame(ventana)
        fecha_frame.pack(pady=10)

        tk.Label(fecha_frame, text="Fecha límite:").pack(side=tk.LEFT)
        entry_fecha = tk.Entry(fecha_frame, textvariable=fecha_var, width=15)
        entry_fecha.pack(side=tk.LEFT, padx=5)
        tk.Button(fecha_frame, text="📅", command=abrir_calendario).pack(side=tk.LEFT)

        return fecha_var

    def agregar_tarea(self):
        ventana = tk.Toplevel(self.root)
        ventana.title("Nueva Tarea")
        ventana.geometry("400x500")

        tk.Label(ventana, text="Título:").pack()
        entry_titulo = tk.Entry(ventana, width=50)
        entry_titulo.pack()

        tk.Label(ventana, text="Descripción:").pack()
        texto = tk.Text(ventana, width=45, height=10)
        texto.pack()

        prioridad_var = self.obtener_prioridad(ventana)
        fecha_var = self.obtener_fecha_calendario(ventana)

        def guardar():
            titulo = entry_titulo.get().strip().title()
            descripcion = texto.get("1.0", tk.END).strip().capitalize()
            prioridad = prioridad_var.get()
            fecha_limite = fecha_var.get()

            if not titulo or not fecha_limite:
                messagebox.showerror("Error", "Faltan datos obligatorios.")
                return

            fecha_creacion = datetime.now().isoformat(sep=' ', timespec='seconds')
            # Dialogo para guardar el archivo en una carpeta
            archivo_guardar = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])

            if archivo_guardar:  # Si el usuario elige un archivo
                with open(archivo_guardar, 'w') as archivo:
                    archivo.write(f"ID: {titulo}\nDescripción: {descripcion}\nPrioridad: {prioridad}\nFecha Limite: {fecha_limite}\nCreación: {fecha_creacion}\n")
                    archivo.write("\n-----\n")  # Separador de tareas

            cursor.execute("INSERT INTO tareas (titulo, descripcion, prioridad, fecha_limite, fecha_creacion, historial_actualizacion) VALUES (?, ?, ?, ?, ?, ?)",
                           (titulo, descripcion, prioridad, fecha_limite, fecha_creacion, ""))
            conn.commit()
            ventana.destroy()
            self.actualizar_lista()

        tk.Button(ventana, text="Guardar Tarea", command=guardar).pack(pady=10)

    def eliminar_tarea(self):
        seleccion = self.lista_tareas.selection()
        if seleccion:
            id_tarea = self.lista_tareas.item(seleccion[0])['values'][0]
            cursor.execute("DELETE FROM tareas WHERE rowid = ?", (id_tarea,))
            conn.commit()
            self.actualizar_lista()

    def actualizar_tarea(self):
        seleccion = self.lista_tareas.selection()
        if not seleccion:
            return

        id_tarea = self.lista_tareas.item(seleccion[0])['values'][0]
        cursor.execute("SELECT titulo, descripcion, prioridad, fecha_limite, historial_actualizacion FROM tareas WHERE rowid = ?", (id_tarea,))
        datos = cursor.fetchone()

        ventana = tk.Toplevel(self.root)
        ventana.title("Actualizar Tarea")
        ventana.geometry("400x500")

        tk.Label(ventana, text="Título:").pack()
        entry_titulo = tk.Entry(ventana, width=50)
        entry_titulo.insert(0, datos[0])
        entry_titulo.pack()

        tk.Label(ventana, text="Descripción:").pack()
        texto = tk.Text(ventana, width=45, height=10)
        texto.insert("1.0", datos[1])
        texto.pack()

        prioridad_var = self.obtener_prioridad(ventana)
        prioridad_var.set(datos[2])

        fecha_var = self.obtener_fecha_calendario(ventana)
        fecha_var.set(datos[3])

        def guardar():
            nuevo_historial = datos[4] + f"\nActualizado: {datetime.now().isoformat(sep=' ', timespec='seconds')}"
            cursor.execute("UPDATE tareas SET titulo=?, descripcion=?, prioridad=?, fecha_limite=?, historial_actualizacion=? WHERE rowid=?",
                           (entry_titulo.get(), texto.get("1.0", tk.END).strip(), prioridad_var.get(), fecha_var.get(), nuevo_historial, id_tarea))
            conn.commit()
            ventana.destroy()
            self.actualizar_lista()

        tk.Button(ventana, text="Guardar Cambios", command=guardar).pack(pady=10)

    def ver_detalles(self):
        seleccion = self.lista_tareas.selection()
        if not seleccion:
            return
        id_tarea = self.lista_tareas.item(seleccion[0])['values'][0]
        cursor.execute("SELECT * FROM tareas WHERE rowid = ?", (id_tarea,))
        datos = cursor.fetchone()

        ventana = tk.Toplevel(self.root)
        ventana.title("📖 Ver Contenido")
        ventana.geometry("620x520")
        ventana.configure(bg="#e8f0fe")

        frame = tk.Frame(ventana, bg="white", bd=2, relief="groove")
        frame.pack(expand=True, fill="both", padx=20, pady=20)

        text_area = tk.Text(frame, wrap="word", bg="white", fg="black", font=("Arial", 11), relief="flat", padx=10, pady=10)

        contenido = (f"""📋 CONTENIDO DE LA TAREA


                     📝 TÍTULO: {datos[1]}


                     📄 DESCRIPCIÓN: {datos[2]}


                     📌 PRIORIDAD: {datos[3]}

                     📅 FECHA LÍMITE: {datos[4]}


                     🕓 CREADO: {datos[5]}

                     📈 HISTORIAL: {datos[6]}""")

        text_area.insert("1.0", contenido)
        text_area.config(state="disabled")
        text_area.pack(expand=True, fill="both")

    def actualizar_lista(self):
        for i in self.lista_tareas.get_children():
            self.lista_tareas.delete(i)
        cursor.execute("SELECT rowid, titulo, prioridad, fecha_limite FROM tareas")
        for fila in cursor.fetchall():
            self.lista_tareas.insert('', 'end', values=(fila[0], fila[1], fila[2], fila[3]))

if __name__ == "__main__":
    root = tk.Tk()
    app = Aplicacion(root)
    root.mainloop()
