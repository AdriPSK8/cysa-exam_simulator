import customtkinter as ctk
from PIL import Image
import json
import random
import os
import pandas as pd
import math
import textwrap  # Importación añadida para ajustar el texto de las opciones en múltiples líneas

COLOR_AZUL_HEADER = "#2b70b0"
COLOR_AZUL_FOOTER = "#005a9c"
COLOR_FONDO_APP = "#ffffff"
COLOR_TEXTO_TIEMPO = "#FFD700"
COLOR_PANEL_LATERAL = "#e0e0e0"
COLOR_BTN_OPCION = "#f0f0f0"
COLOR_VERDE_CORRECTO = "#28a745"
COLOR_ROJO_INCORRECTO = "#dc3545"
COLOR_PANEL_MEDIA = "#f7f7f7"

FONT_TITULO_MENU = ("Arial", 34, "bold")
FONT_BOTON_MENU = ("Arial", 17, "bold")
FONT_HEADER = ("Arial", 19, "bold")
FONT_PROGRESO = ("Arial", 15, "bold")
FONT_TIEMPO = ("Arial", 17, "bold")
FONT_PREGUNTA = ("Arial", 17)
FONT_OPCION = ("Arial", 15)
FONT_ETIQUETA = ("Arial", 15, "bold")
FONT_EXPLICACION = ("Arial", 17)
FONT_TABLA = ("Courier", 12)
FONT_TABLA_GRANDE = ("Courier", 13)
FONT_NOTAS = ("Arial", 14)

OBJETIVO_A_CARPETA = {
    "Security Operations": "objetivo1",
    "Vulnerability Management": "objetivo2",
    "Incident Response Management": "objetivo3",
    "Reporting and Communication": "objetivo4",
    "Practica1": "practica1",
    "Practica2": "practica2",
}

OBJETIVO_A_ARCHIVO = {
    "Security Operations": "objetivo1_security_operations.json",
    "Vulnerability Management": "objetivo2_vulnerability_management.json",
    "Incident Response Management": "objetivo3_incident_response.json",
    "Reporting and Communication": "objetivo4_reporting.json",
    "Practica1": "practica1_examen.json",
    "Practica2": "practica2_examen.json",
}

TIPO_EXAMEN = {
    "normal": 0,
    "objetivo": 0,
    "real": 165,
    "practica1": 165,
    "practica2": 165,
}

def limpiar_texto_pregunta(texto):
    if not texto:
        return ""
    lineas = []
    for linea in texto.split("\n"):
        t = linea.strip()
        if t.startswith(("A)", "B)", "C)", "D)", "A.", "B.", "C.", "D.", "1)", "2)", "3)", "4)")):
            continue
        lineas.append(linea)
    return "\n".join(lineas).strip()

def carpeta_objetivo(pregunta):
    return OBJETIVO_A_CARPETA.get(pregunta.get("objetivo", ""), "objetivo1")

def limpiar_frame(frame):
    for w in frame.winfo_children():
        w.destroy()

def leer_tabla(ruta):
    ext = os.path.splitext(ruta)[1].lower()

    if ext in [".xlsx", ".xls"]:
        return pd.read_excel(ruta)

    if ext == ".csv":
        return pd.read_csv(ruta)

    if ext == ".txt":
        try:
            return pd.read_csv(ruta, sep=None, engine="python")
        except Exception:
            try:
                return pd.read_table(ruta, sep=r"\s+", engine="python")
            except Exception:
                return pd.read_fwf(ruta)

    raise ValueError(f"Formato no soportado: {ext}")

def calcular_altura_opcion(texto, chars_por_linea=75, alto_minimo=45, alto_por_linea=28):
    if not texto:
        return alto_minimo
    # CORRECCIÓN: Usamos textwrap para calcular la cantidad real de líneas que se generarán
    lineas = len(textwrap.wrap(texto, width=chars_por_linea))
    return max(alto_minimo, lineas * alto_por_linea)

class ExamenApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Simulador Examen CySA+ V3")
        self.geometry("1100x750")
        ctk.set_appearance_mode("light")

        self.data = self.cargar_todas_preguntas()
        print(f"✓ Total preguntas cargadas: {len(self.data)}")

        self.idx = 0
        self.preguntas_actuales = []
        self.respuestas_usuario = []
        self.sidebar_visible = False
        self.tiempo_restante = 0
        self.timer_id = None
        self.modo_actual = ""

        self.menu_inicial()

    def cargar_todas_preguntas(self):
        todas = []
        carpeta = "preguntas"

        if not os.path.exists(carpeta):
            print(f"⚠️ Error: La carpeta '{carpeta}' no existe")
            return todas

        archivos_found = 0
        resumen_objetivos = {}

        for nombre_archivo in os.listdir(carpeta):
            if nombre_archivo.endswith(".json"):
                ruta = os.path.join(carpeta, nombre_archivo)
                try:
                    with open(ruta, "r", encoding="utf-8") as f:
                        datos = json.load(f)
                        todas.extend(datos)
                        archivos_found += 1

                        for p in datos:
                            obj = p.get("objetivo", "Unknown")
                            resumen_objetivos[obj] = resumen_objetivos.get(obj, 0) + 1

                        print(f"  ✓ Cargado: {nombre_archivo} ({len(datos)} preguntas)")
                except json.JSONDecodeError as e:
                    print(f"  ⚠️ Error JSON en {nombre_archivo}: {e}")
                except Exception as e:
                    print(f"  ⚠️ Error cargando {nombre_archivo}: {e}")

        if archivos_found == 0:
            print(f"  ⚠️ No se encontraron archivos JSON en '{carpeta}'")

        print(f"\n📊 Resumen de objetivos encontrados:")
        for obj, count in resumen_objetivos.items():
            print(f"   • {obj}: {count} preguntas")
        print()

        return todas

    def menu_inicial(self):
        self.detener_temporizador()
        for widget in self.winfo_children():
            widget.destroy()

        self.sidebar_visible = False
        self.menu_frame = ctk.CTkFrame(self, fg_color=COLOR_FONDO_APP)
        self.menu_frame.pack(expand=True, fill="both")

        ctk.CTkLabel(
            self.menu_frame,
            text="SIMULADOR CySA+ V3",
            font=FONT_TITULO_MENU,
            text_color=COLOR_AZUL_HEADER
        ).pack(pady=40)

        btn_config = {
            "width": 450,
            "height": 60,
            "font": FONT_BOTON_MENU,
            "fg_color": COLOR_AZUL_HEADER
        }

        if os.path.exists("sesion.json"):
            ctk.CTkButton(
                self.menu_frame,
                text="▶ Reanudar Sesión Guardada",
                command=self.cargar_sesion,
                fg_color="#28a745",
                width=450,
                height=60,
                font=FONT_BOTON_MENU
            ).pack(pady=10)

        ctk.CTkButton(
            self.menu_frame,
            text="1) Examen Normal (Todas las preguntas)",
            command=lambda: self.preparar_examen("normal"),
            **btn_config
        ).pack(pady=10)

        ctk.CTkButton(
            self.menu_frame,
            text="2) Examen por Objetivos",
            command=self.mostrar_objetivos,
            **btn_config
        ).pack(pady=10)

        ctk.CTkButton(
            self.menu_frame,
            text="3) Examen Estilo Real (85 Preguntas - 165 min)",
            command=lambda: self.preparar_examen("real"),
            **btn_config
        ).pack(pady=10)

        ctk.CTkButton(
            self.menu_frame,
            text="4) Examen Práctica 1 (165 min)",
            command=lambda: self.preparar_examen("practica1"),
            **btn_config
        ).pack(pady=10)

        ctk.CTkButton(
            self.menu_frame,
            text="5) Examen Práctica 2 (165 min)",
            command=lambda: self.preparar_examen("practica2"),
            **btn_config
        ).pack(pady=10)

        ctk.CTkButton(
            self.menu_frame,
            text="Salir del Simulador",
            command=self.destroy,
            width=450,
            height=50,
            fg_color="#666666",
            font=("Arial", 16)
        ).pack(pady=30)

    def mostrar_objetivos(self):
        for w in self.menu_frame.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self.menu_frame,
            text="Selecciona un Objetivo",
            font=("Arial", 24, "bold"),
            text_color=COLOR_AZUL_HEADER
        ).pack(pady=30)

        objs = [
            "Security Operations",
            "Vulnerability Management",
            "Incident Response Management",
            "Reporting and Communication"
        ]

        for o in objs:
            count = len([p for p in self.data if p.get("objetivo") == o])
            ctk.CTkButton(
                self.menu_frame,
                text=f"{o} ({count} preguntas)",
                width=450,
                height=50,
                fg_color=COLOR_AZUL_HEADER,
                font=("Arial", 16, "bold"),
                command=lambda obj=o: self.preparar_examen("objetivo", obj)
            ).pack(pady=10)

        ctk.CTkButton(
            self.menu_frame,
            text="Volver al Menú",
            command=self.menu_inicial,
            width=450,
            height=50,
            fg_color="#666666",
            font=("Arial", 16, "bold")
        ).pack(pady=20)

    def preparar_examen(self, modo, filtro=None):
        self.modo_actual = modo

        if modo == "normal":
            self.preguntas_actuales = list(self.data)
            self.tiempo_restante = 0
        elif modo == "objetivo":
            self.preguntas_actuales = [p for p in self.data if p.get("objetivo") == filtro]
            self.tiempo_restante = 0
        elif modo == "real":
            self.preguntas_actuales = self.generar_examen_real()
            self.tiempo_restante = TIPO_EXAMEN["real"] * 60
        elif modo == "practica1":
            self.preguntas_actuales = [p for p in self.data if p.get("objetivo") == "Practica1"]
            self.tiempo_restante = TIPO_EXAMEN["practica1"] * 60
        elif modo == "practica2":
            self.preguntas_actuales = [p for p in self.data if p.get("objetivo") == "Practica2"]
            self.tiempo_restante = TIPO_EXAMEN["practica2"] * 60

        self.idx = 0
        self.respuestas_usuario = [None] * len(self.preguntas_actuales)
        self.iniciar_interfaz_examen()

    def generar_examen_real(self):
        dist = {
            "Security Operations": 28,
            "Vulnerability Management": 26,
            "Incident Response Management": 19,
            "Reporting and Communication": 12
        }

        seleccion = []
        usados = set()

        for obj, cantidad in dist.items():
            pool = [p for p in self.data if p.get("objetivo") == obj]
            random.shuffle(pool)
            count = 0
            for p in pool:
                if p.get("id") in usados:
                    continue
                seleccion.append(p)
                usados.add(p.get("id"))
                count += 1
                if count >= cantidad:
                    break

        random.shuffle(seleccion)
        return seleccion[:85]

    def guardar_sesion(self):
        estado = {
            "modo": self.modo_actual,
            "idx": self.idx,
            "tiempo_restante": self.tiempo_restante,
            "preguntas": self.preguntas_actuales,
            "respuestas_usuario": self.respuestas_usuario
        }
        with open("sesion.json", "w", encoding="utf-8") as f:
            json.dump(estado, f, ensure_ascii=False, indent=2)
        self.menu_inicial()

    def cargar_sesion(self):
        try:
            with open("sesion.json", "r", encoding="utf-8") as f:
                estado = json.load(f)

            self.modo_actual = estado.get("modo", "")
            self.idx = estado.get("idx", 0)
            self.tiempo_restante = estado.get("tiempo_restante", 0)
            self.preguntas_actuales = estado.get("preguntas", [])
            self.respuestas_usuario = estado.get("respuestas_usuario", [None] * len(self.preguntas_actuales))

            if len(self.respuestas_usuario) != len(self.preguntas_actuales):
                self.respuestas_usuario = [None] * len(self.preguntas_actuales)

            self.iniciar_interfaz_examen()
        except Exception as e:
            print("Error cargando sesión:", e)

    def iniciar_interfaz_examen(self):
        self.detener_temporizador()
        for widget in self.winfo_children():
            widget.destroy()

        self.sidebar_visible = False

        self.header_frame = ctk.CTkFrame(self, height=50, fg_color=COLOR_AZUL_HEADER, corner_radius=0)
        self.header_frame.pack(side="top", fill="x")

        self.btn_toggle = ctk.CTkButton(
            self.header_frame,
            text="☰ Preguntas",
            width=100,
            fg_color="transparent",
            border_color="white",
            border_width=1,
            font=("Arial", 14, "bold"),
            command=self.toggle_sidebar
        )
        self.btn_toggle.pack(side="left", padx=10, pady=10)

        nombres_modo = {
            "normal": "Examen Normal",
            "objetivo": "Examen por Objetivos",
            "real": "Examen Estilo Real",
            "practica1": "Examen Práctica 1",
            "practica2": "Examen Práctica 2"
        }
        nombre_examen = nombres_modo.get(self.modo_actual, "Examen")

        ctk.CTkLabel(
            self.header_frame,
            text=f"Exam - CompTIA CySA+ - {nombre_examen}",
            font=FONT_HEADER,
            text_color="white"
        ).pack(side="left", padx=20)

        self.lbl_progreso = ctk.CTkLabel(
            self.header_frame,
            text="",
            font=FONT_PROGRESO,
            text_color="white"
        )
        self.lbl_progreso.pack(side="right", padx=20)

        self.lbl_tiempo = ctk.CTkLabel(
            self.header_frame,
            text="",
            font=FONT_TIEMPO,
            text_color=COLOR_TEXTO_TIEMPO
        )
        self.lbl_tiempo.pack(side="right", padx=10)

        self.footer_frame = ctk.CTkFrame(self, height=50, fg_color=COLOR_AZUL_FOOTER, corner_radius=0)
        self.footer_frame.pack(side="bottom", fill="x")

        ctk.CTkButton(
            self.footer_frame,
            text="Salir",
            width=80,
            fg_color="#d9534f",
            font=("Arial", 14, "bold"),
            command=self.menu_inicial
        ).pack(side="left", padx=10, pady=10)

        ctk.CTkButton(
            self.footer_frame,
            text="Pausa (Guardar)",
            width=120,
            fg_color="#f0ad4e",
            text_color="black",
            font=("Arial", 14, "bold"),
            command=self.guardar_sesion
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            self.footer_frame,
            text="Repetir Examen",
            width=120,
            fg_color="#5bc0de",
            text_color="black",
            font=("Arial", 14, "bold"),
            command=lambda: self.preparar_examen(self.modo_actual)
        ).pack(side="left", padx=10)

        self.btn_next = ctk.CTkButton(
            self.footer_frame,
            text="Next ➔",
            width=100,
            fg_color="transparent",
            border_color="white",
            border_width=1,
            font=("Arial", 14, "bold"),
            command=lambda: self.ir_a(self.idx + 1)
        )
        self.btn_next.pack(side="right", padx=10, pady=10)

        self.btn_prev = ctk.CTkButton(
            self.footer_frame,
            text="⬅ Previous",
            width=100,
            fg_color="transparent",
            border_color="white",
            border_width=1,
            font=("Arial", 14, "bold"),
            command=lambda: self.ir_a(self.idx - 1)
        )
        self.btn_prev.pack(side="right", padx=10)

        self.body_frame = ctk.CTkFrame(self, fg_color=COLOR_FONDO_APP)
        self.body_frame.pack(side="top", expand=True, fill="both")

        self.sidebar = ctk.CTkScrollableFrame(self.body_frame, width=200, fg_color=COLOR_PANEL_LATERAL, corner_radius=0)
        self.botones_nav = []
        for i in range(len(self.preguntas_actuales)):
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"Pregunta {i+1}",
                fg_color="transparent",
                text_color="black",
                anchor="w",
                font=("Arial", 13),
                command=lambda i=i: self.ir_a(i)
            )
            btn.pack(fill="x", pady=2, padx=5)
            self.botones_nav.append(btn)

        self.content_area = ctk.CTkScrollableFrame(self.body_frame, fg_color="transparent")
        self.content_area.pack(side="right", expand=True, fill="both", padx=20, pady=20)

        self.question_container = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.question_container.pack(fill="both", expand=True)

        self.question_container.grid_columnconfigure(0, weight=1, uniform="cols")
        self.question_container.grid_columnconfigure(1, weight=1, uniform="cols")
        self.question_container.grid_rowconfigure(0, weight=1)

        self.question_left = ctk.CTkFrame(self.question_container, fg_color="transparent")
        self.question_left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.question_right = ctk.CTkScrollableFrame(self.question_container, fg_color=COLOR_PANEL_MEDIA, corner_radius=8)

        if self.tiempo_restante > 0:
            self.actualizar_temporizador()
        else:
            self.lbl_tiempo.configure(text="")

        self.cargar_pregunta()

    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar.pack_forget()
        else:
            self.sidebar.pack(side="left", fill="y")
        self.sidebar_visible = not self.sidebar_visible

    def actualizar_temporizador(self):
        self.detener_temporizador()
        if self.tiempo_restante > 0:
            horas = self.tiempo_restante // 3600
            minutos = (self.tiempo_restante % 3600) // 60
            segs = self.tiempo_restante % 60
            self.lbl_tiempo.configure(text=f"Time Remaining {horas:02d}:{minutos:02d}:{segs:02d}")
            self.tiempo_restante -= 1
            self.timer_id = self.after(1000, self.actualizar_temporizador)
        else:
            self.lbl_tiempo.configure(text="TIEMPO AGOTADO")
            self.mostrar_popup_tiempo()

    def detener_temporizador(self):
        if self.timer_id is not None:
            try:
                self.after_cancel(self.timer_id)
            except Exception:
                pass
            self.timer_id = None

    def mostrar_popup_tiempo(self):
        pop = ctk.CTkToplevel(self)
        pop.title("Tiempo Finalizado")
        ctk.CTkLabel(pop, text="El tiempo del examen ha finalizado.", font=("Arial", 18, "bold")).pack(padx=40, pady=40)
        ctk.CTkButton(pop, text="Finalizar", command=lambda: [pop.destroy(), self.menu_inicial()]).pack(pady=10)
        pop.grab_set()

    def cargar_pregunta(self):
        if not self.preguntas_actuales:
            return

        self.btn_prev.configure(state="normal" if self.idx > 0 else "disabled")
        self.btn_next.configure(state="normal" if self.idx < len(self.preguntas_actuales) - 1 else "disabled")
        self.lbl_progreso.configure(text=f"Question {self.idx + 1} of {len(self.preguntas_actuales)}")

        p = self.preguntas_actuales[self.idx]
        texto_pregunta = limpiar_texto_pregunta(p.get("pregunta", ""))

        limpiar_frame(self.question_left)
        limpiar_frame(self.question_right)
        self.question_right.grid_forget()

        lbl_preg = ctk.CTkLabel(
            self.question_left,
            text=texto_pregunta,
            font=FONT_PREGUNTA,
            justify="left",
            anchor="w",
            wraplength=820
        )
        lbl_preg.pack(anchor="nw", fill="x", pady=(0, 10))

        respuesta_previa = self.respuestas_usuario[self.idx]
        respuesta_correcta = str(p.get("respuesta", "")).strip().upper()

        ctk.CTkLabel(
            self.question_left,
            text="Respuestas",
            font=FONT_ETIQUETA,
            text_color=COLOR_AZUL_HEADER
        ).pack(anchor="w", pady=(5, 6))

        for opt in p.get("opciones", []):
            opt_str = str(opt).strip()
            if ")" in opt_str:
                letra = opt_str.split(")")[0].strip().upper()
            elif "." in opt_str[:3]:
                letra = opt_str.split(".")[0].strip().upper()
            else:
                letra = opt_str[0].upper() if opt_str else ""

            # CORRECCIÓN: Ajustamos el texto de la opción con textwrap para que no se corte
            ancho_linea = 75
            opt_str_wrapped = textwrap.fill(opt_str, width=ancho_linea)

            btn_color = COLOR_BTN_OPCION
            estado = "normal"
            text_color = "black"

            if respuesta_previa is not None:
                estado = "disabled"
                if letra == respuesta_correcta:
                    btn_color = COLOR_VERDE_CORRECTO
                    text_color = "white"
                elif letra == respuesta_previa:
                    btn_color = COLOR_ROJO_INCORRECTO
                    text_color = "white"

            # Pasamos el ancho de línea a la función para un cálculo perfecto de altura
            alto_btn = calcular_altura_opcion(opt_str, chars_por_linea=ancho_linea)

            btn = ctk.CTkButton(
                self.question_left,
                text=opt_str_wrapped,  # Pasamos el texto formateado
                font=FONT_OPCION,
                height=alto_btn,
                anchor="w",
                fg_color=btn_color,
                text_color=text_color,
                hover_color="#d0d0d0",
                state=estado,
                command=lambda l=letra: self.procesar_respuesta(l)
            )
            
            # CORRECCIÓN: Forzamos la justificación a la izquierda dentro de la etiqueta interna del CTkButton
            try:
                btn._text_label.configure(justify="left")
            except Exception:
                pass

            btn.pack(anchor="w", pady=3, fill="x")

        if p.get("imagen") or p.get("tabla"):
            self.question_right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
            ctk.CTkLabel(
                self.question_right,
                text="Contenido asociado",
                font=FONT_ETIQUETA,
                text_color=COLOR_AZUL_HEADER
            ).pack(anchor="w", padx=12, pady=(12, 8))
            self.mostrar_media_en_panel(p)

        self.actualizar_color_sidebar()

    def mostrar_media_en_panel(self, p):
        base = carpeta_objetivo(p)

        if p.get("imagen"):
            try:
                ruta = os.path.join("img", base, p["imagen"])
                img = Image.open(ruta)
                img.thumbnail((360, 250))
                ctk_img = ctk.CTkImage(light_image=img, size=(img.width, img.height))
                lbl = ctk.CTkLabel(self.question_right, image=ctk_img, text="", cursor="hand2")
                lbl.pack(padx=12, pady=8)
                lbl.image = ctk_img
                lbl.bind("<Button-1>", lambda e, ruta=ruta: self.abrir_imagen_ampliada(ruta))
            except Exception as e:
                ctk.CTkLabel(self.question_right, text=f"Error imagen: {e}", text_color="red", wraplength=300).pack(padx=12, pady=8, anchor="w")

        if p.get("tabla"):
            ruta = os.path.join("data", base, p["tabla"])
            txt = ctk.CTkTextbox(self.question_right, width=360, height=250, font=FONT_TABLA, wrap="none")
            txt.pack(padx=12, pady=8, fill="both", expand=False)
            try:
                df = leer_tabla(ruta)
                txt.insert("0.0", df.to_string(index=False))
            except Exception as e:
                txt.insert("0.0", f"Error al cargar tabla:\n{e}")
            txt.configure(state="disabled")

    def abrir_imagen_ampliada(self, ruta):
        pop = ctk.CTkToplevel(self)
        pop.title("Imagen ampliada")
        pop.geometry("1000x700")
        pop.attributes("-topmost", True)

        try:
            img = Image.open(ruta)
            img.thumbnail((950, 650))
            ctk_img = ctk.CTkImage(light_image=img, size=(img.width, img.height))
            lbl = ctk.CTkLabel(pop, image=ctk_img, text="")
            lbl.pack(expand=True, padx=20, pady=20)
            lbl.image = ctk_img
        except Exception as e:
            ctk.CTkLabel(pop, text=f"Error al abrir imagen:\n{e}", text_color="red").pack(pady=40)

        pop.grab_set()

    def procesar_respuesta(self, eleccion):
        self.respuestas_usuario[self.idx] = eleccion
        p = self.preguntas_actuales[self.idx]
        es_correcta = (eleccion == str(p.get("respuesta", "")).strip().upper())
        self.cargar_pregunta()
        self.mostrar_popup_explicacion(es_correcta, p.get("explicacion", "No hay explicación disponible."))

    def actualizar_color_sidebar(self):
        for i, estado in enumerate(self.respuestas_usuario):
            if estado is not None and i < len(self.botones_nav):
                p = self.preguntas_actuales[i]
                if estado == str(p.get("respuesta", "")).strip().upper():
                    self.botones_nav[i].configure(text_color=COLOR_VERDE_CORRECTO)
                else:
                    self.botones_nav[i].configure(text_color=COLOR_ROJO_INCORRECTO)

    def ir_a(self, index):
        if 0 <= index < len(self.preguntas_actuales):
            self.idx = index
            self.cargar_pregunta()

    def mostrar_popup_explicacion(self, es_correcta, exp):
        pop = ctk.CTkToplevel(self)
        pop.geometry("650x430")
        pop.title("Explanation")
        pop.attributes("-topmost", True)
        pop.configure(fg_color=COLOR_VERDE_CORRECTO if es_correcta else COLOR_ROJO_INCORRECTO)

        ctk.CTkButton(
            pop,
            text="✕",
            width=30,
            fg_color="transparent",
            text_color="white",
            hover_color="#555555",
            command=pop.destroy
        ).pack(anchor="ne", padx=5, pady=5)

        ctk.CTkLabel(
            pop,
            text="CORRECTO" if es_correcta else "INCORRECTO",
            font=("Arial", 24, "bold"),
            text_color="white"
        ).pack(pady=5)

        exp_limpia = "\n".join([linea.strip() for linea in exp.split("\n")])
        txt_exp = ctk.CTkTextbox(pop, font=FONT_EXPLICACION, text_color="white", fg_color="transparent", wrap="word")
        txt_exp.pack(padx=20, pady=10, fill="both", expand=True)
        txt_exp.insert("0.0", exp_limpia)
        txt_exp.configure(state="disabled")

        btn_frame = ctk.CTkFrame(pop, fg_color="transparent")
        btn_frame.pack(pady=10)

        if self.idx < len(self.preguntas_actuales) - 1:
            ctk.CTkButton(
                btn_frame,
                text="Siguiente Pregunta ➔",
                fg_color="white",
                text_color="black",
                hover_color="#e0e0e0",
                font=("Arial", 14, "bold"),
                command=lambda: [pop.destroy(), self.ir_a(self.idx + 1)]
            ).pack()
        else:
            ctk.CTkButton(
                btn_frame,
                text="Cerrar",
                fg_color="white",
                text_color="black",
                hover_color="#e0e0e0",
                font=("Arial", 14, "bold"),
                command=pop.destroy
            ).pack()

        pop.grab_set()

    def abrir_media(self, tipo, base, nombre_archivo):
        pop = ctk.CTkToplevel(self)
        pop.geometry("800x500")
        pop.attributes("-topmost", True)

        try:
            if tipo == "img":
                pop.title("Visor de Imagen")
                ruta = os.path.join("img", base, nombre_archivo)
                img = Image.open(ruta)
                img.thumbnail((750, 450))
                ctk_img = ctk.CTkImage(light_image=img, size=(img.width, img.height))
                ctk.CTkLabel(pop, image=ctk_img, text="").pack(expand=True)
                pop.image = ctk_img

            elif tipo == "data":
                pop.title("Visor de Tabla (Excel/CSV/TXT)")
                txt = ctk.CTkTextbox(pop, width=750, height=450, font=FONT_TABLA_GRANDE, wrap="none")
                txt.pack(padx=20, pady=20, fill="both", expand=True)
                ruta = os.path.join("data", base, nombre_archivo)
                try:
                    df = leer_tabla(ruta)
                    txt.insert("0.0", df.to_string(index=False))
                except ImportError:
                    txt.insert("0.0", "⚠️ ERROR:\nInstala pandas y openpyxl.\n\npip install pandas openpyxl")
                except FileNotFoundError:
                    txt.insert("0.0", f"⚠️ Archivo no encontrado en la ruta:\n{ruta}")
                except Exception as e:
                    txt.insert("0.0", f"Error inesperado al cargar el archivo:\n{e}")
                txt.configure(state="disabled")

            elif tipo == "txt":
                pop.title("Visor de Notas")
                ruta = os.path.join("data", base, nombre_archivo)
                txt = ctk.CTkTextbox(pop, width=750, height=450, font=FONT_NOTAS, wrap="word")
                txt.pack(padx=20, pady=20, fill="both", expand=True)
                with open(ruta, encoding="utf-8") as f:
                    txt.insert("0.0", f.read())
                txt.configure(state="disabled")

        except Exception as e:
            ctk.CTkLabel(pop, text=f"Error al cargar archivo:\n{e}", text_color="red").pack(pady=50)

if __name__ == "__main__":
    app = ExamenApp()
    app.mainloop()