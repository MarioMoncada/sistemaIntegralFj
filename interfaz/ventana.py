"""
Interfaz grafica (tkinter) del sistema Software FJ.

Cada accion del usuario se ejecuta dentro de try/except: los errores se
muestran en un cuadro de dialogo y se escriben en la bitacora, pero la
ventana nunca se cierra por una excepcion.
"""
import tkinter as tk
from tkinter import messagebox, ttk

from excepciones.errores import ErrorSistemaFJ
from gestion.sistema import TIPOS_SERVICIO
from modelo.cliente import CATEGORIAS
from simulacion import ejecutar_simulacion
from utilidades.registro import leer_bitacora, registrar_error, registrar_evento

# Etiquetas de los dos campos adicionales de cada tipo de servicio
CAMPOS_SERVICIO = {
    "sala": ("Capacidad (personas)", "Ubicacion"),
    "equipo": ("Cantidad de equipos", "Tipo de equipo"),
    "asesoria": ("Especialidad", "Nivel (junior/senior/experto)"),
}


class VentanaPrincipal(tk.Tk):
    """Ventana principal con pestanas de clientes, servicios, reservas y bitacora."""

    def __init__(self, sistema):
        super().__init__()
        self.sistema = sistema
        self.title("Software FJ - Gestion de Clientes, Servicios y Reservas")
        self.geometry("980x620")
        self.minsize(860, 560)

        self._construir_cabecera()
        self.cuaderno = ttk.Notebook(self)
        self.cuaderno.pack(fill="both", expand=True, padx=10, pady=5)
        self._construir_pestana_clientes()
        self._construir_pestana_servicios()
        self._construir_pestana_reservas()
        self._construir_pestana_bitacora()
        self._construir_barra_estado()

        self.refrescar_todo()
        registrar_evento("Interfaz grafica iniciada")

    # =========================== utilidades ===========================
    def _construir_cabecera(self):
        marco = tk.Frame(self, bg="#1f3b57")
        marco.pack(fill="x")
        tk.Label(
            marco,
            text="Software FJ",
            bg="#1f3b57",
            fg="white",
            font=("Segoe UI", 16, "bold"),
        ).pack(side="left", padx=12, pady=8)
        tk.Label(
            marco,
            text="Sistema integral de clientes, servicios y reservas",
            bg="#1f3b57",
            fg="#cfe0ef",
            font=("Segoe UI", 10),
        ).pack(side="left", pady=10)

    def _construir_barra_estado(self):
        self.estado = tk.StringVar(value="Sistema listo.")
        tk.Label(
            self, textvariable=self.estado, anchor="w", relief="sunken", bd=1, padx=6
        ).pack(fill="x", side="bottom")

    def _informar(self, texto):
        self.estado.set(texto)

    def _manejar_error(self, titulo, excepcion):
        """Punto unico de manejo de errores de la interfaz."""
        registrar_error(f"[GUI] {titulo}", excepcion)
        detalle = str(excepcion)
        causa = excepcion.__cause__
        if causa is not None:
            detalle += f"\n\nCausa original: {type(causa).__name__}: {causa}"
        messagebox.showerror(titulo, detalle)
        self._informar(f"Error: {excepcion}")

    @staticmethod
    def _crear_tabla(padre, columnas, anchos):
        contenedor = tk.Frame(padre)
        contenedor.pack(fill="both", expand=True, padx=8, pady=8)
        tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", height=10)
        for columna, ancho in zip(columnas, anchos):
            tabla.heading(columna, text=columna)
            tabla.column(columna, width=ancho, anchor="w")
        barra = ttk.Scrollbar(contenedor, orient="vertical", command=tabla.yview)
        tabla.configure(yscroll=barra.set)
        tabla.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        return tabla

    @staticmethod
    def _campo(padre, etiqueta, fila, columna=0, ancho=24, variable=None):
        tk.Label(padre, text=etiqueta).grid(row=fila, column=columna, sticky="e", padx=5, pady=4)
        entrada = tk.Entry(padre, width=ancho, textvariable=variable)
        entrada.grid(row=fila, column=columna + 1, sticky="w", padx=5, pady=4)
        return entrada

    # =========================== CLIENTES ===========================
    def _construir_pestana_clientes(self):
        pestana = tk.Frame(self.cuaderno)
        self.cuaderno.add(pestana, text="Clientes")

        formulario = tk.LabelFrame(pestana, text="Registrar cliente", padx=8, pady=8)
        formulario.pack(fill="x", padx=8, pady=8)

        self.cli_nombre = self._campo(formulario, "Nombre:", 0)
        self.cli_documento = self._campo(formulario, "Documento:", 1)
        self.cli_email = self._campo(formulario, "Correo:", 0, 2)
        self.cli_telefono = self._campo(formulario, "Telefono:", 1, 2)

        tk.Label(formulario, text="Categoria:").grid(row=2, column=0, sticky="e", padx=5, pady=4)
        self.cli_categoria = ttk.Combobox(
            formulario, values=list(CATEGORIAS), state="readonly", width=21
        )
        self.cli_categoria.current(0)
        self.cli_categoria.grid(row=2, column=1, sticky="w", padx=5, pady=4)

        tk.Button(
            formulario, text="Registrar cliente", width=18, command=self.accion_registrar_cliente
        ).grid(row=2, column=3, padx=5, pady=4, sticky="w")

        self.tabla_clientes = self._crear_tabla(
            pestana,
            ("ID", "Nombre", "Documento", "Correo", "Telefono", "Categoria", "Reservas"),
            (70, 180, 110, 200, 110, 100, 80),
        )

    def accion_registrar_cliente(self):
        try:
            cliente = self.sistema.registrar_cliente(
                self.cli_nombre.get(),
                self.cli_documento.get(),
                self.cli_email.get(),
                self.cli_telefono.get(),
                self.cli_categoria.get(),
            )
        except ErrorSistemaFJ as exc:
            self._manejar_error("No fue posible registrar el cliente", exc)
        else:
            for entrada in (self.cli_nombre, self.cli_documento, self.cli_email, self.cli_telefono):
                entrada.delete(0, tk.END)
            self._informar(f"Cliente {cliente.identificador} registrado correctamente.")
            self.refrescar_todo()

    # =========================== SERVICIOS ===========================
    def _construir_pestana_servicios(self):
        pestana = tk.Frame(self.cuaderno)
        self.cuaderno.add(pestana, text="Servicios")

        formulario = tk.LabelFrame(pestana, text="Crear servicio", padx=8, pady=8)
        formulario.pack(fill="x", padx=8, pady=8)

        tk.Label(formulario, text="Tipo:").grid(row=0, column=0, sticky="e", padx=5, pady=4)
        self.srv_tipo = ttk.Combobox(
            formulario, values=list(TIPOS_SERVICIO), state="readonly", width=21
        )
        self.srv_tipo.current(0)
        self.srv_tipo.grid(row=0, column=1, sticky="w", padx=5, pady=4)
        self.srv_tipo.bind("<<ComboboxSelected>>", lambda _evento: self._actualizar_etiquetas())

        self.srv_nombre = self._campo(formulario, "Nombre:", 1)
        self.srv_costo = self._campo(formulario, "Costo base:", 2)

        self.etiqueta_extra1 = tk.Label(formulario, text="Capacidad (personas):")
        self.etiqueta_extra1.grid(row=0, column=2, sticky="e", padx=5, pady=4)
        self.srv_extra1 = tk.Entry(formulario, width=24)
        self.srv_extra1.grid(row=0, column=3, sticky="w", padx=5, pady=4)

        self.etiqueta_extra2 = tk.Label(formulario, text="Ubicacion:")
        self.etiqueta_extra2.grid(row=1, column=2, sticky="e", padx=5, pady=4)
        self.srv_extra2 = tk.Entry(formulario, width=24)
        self.srv_extra2.grid(row=1, column=3, sticky="w", padx=5, pady=4)

        tk.Button(
            formulario, text="Crear servicio", width=18, command=self.accion_crear_servicio
        ).grid(row=2, column=3, padx=5, pady=4, sticky="w")

        self.tabla_servicios = self._crear_tabla(
            pestana,
            ("ID", "Tipo", "Nombre", "Costo base", "Unidad", "Estado", "Detalle"),
            (70, 120, 170, 100, 70, 100, 300),
        )

        botones = tk.Frame(pestana)
        botones.pack(fill="x", padx=8, pady=(0, 8))
        tk.Button(
            botones,
            text="Activar / desactivar servicio",
            command=self.accion_alternar_disponibilidad,
        ).pack(side="left", padx=4)
        tk.Button(botones, text="Cotizar servicio...", command=self.accion_cotizar).pack(
            side="left", padx=4
        )

    def _actualizar_etiquetas(self):
        etiquetas = CAMPOS_SERVICIO.get(self.srv_tipo.get(), ("Parametro 1", "Parametro 2"))
        self.etiqueta_extra1.config(text=f"{etiquetas[0]}:")
        self.etiqueta_extra2.config(text=f"{etiquetas[1]}:")

    def accion_crear_servicio(self):
        try:
            servicio = self.sistema.registrar_servicio(
                self.srv_tipo.get(),
                self.srv_nombre.get(),
                self.srv_costo.get(),
                self.srv_extra1.get(),
                self.srv_extra2.get(),
            )
        except ErrorSistemaFJ as exc:
            self._manejar_error("No fue posible crear el servicio", exc)
        else:
            for entrada in (self.srv_nombre, self.srv_costo, self.srv_extra1, self.srv_extra2):
                entrada.delete(0, tk.END)
            self._informar(f"Servicio {servicio.identificador} creado correctamente.")
            self.refrescar_todo()

    def _servicio_seleccionado(self):
        seleccion = self.tabla_servicios.selection()
        if not seleccion:
            messagebox.showinfo("Seleccion requerida", "Seleccione un servicio de la tabla.")
            return None
        return self.tabla_servicios.item(seleccion[0], "values")[0]

    def accion_alternar_disponibilidad(self):
        identificador = self._servicio_seleccionado()
        if not identificador:
            return
        try:
            disponible = self.sistema.alternar_disponibilidad(identificador)
        except ErrorSistemaFJ as exc:
            self._manejar_error("No fue posible cambiar la disponibilidad", exc)
        else:
            estado = "disponible" if disponible else "no disponible"
            self._informar(f"El servicio {identificador} ahora esta {estado}.")
            self.refrescar_todo()

    def accion_cotizar(self):
        """Muestra el desglose usando los metodos sobrecargados de costos."""
        identificador = self._servicio_seleccionado()
        if not identificador:
            return
        try:
            servicio = self.sistema.buscar_servicio(identificador)
            duracion = self._pedir_entero(
                f"Duracion en {servicio.unidad}(s) para {servicio.nombre}"
            )
            if duracion is None:
                return
            detalle = servicio.desglose(duracion)
            paquete = servicio.cotizar([duracion, duracion])
        except ErrorSistemaFJ as exc:
            self._manejar_error("No fue posible cotizar el servicio", exc)
        else:
            messagebox.showinfo(
                f"Cotizacion {identificador}",
                f"Subtotal: ${detalle['subtotal']:,.2f}\n"
                f"Adicionales: ${detalle['adicionales']:,.2f}\n"
                f"Descuento: ${detalle['descuento']:,.2f}\n"
                f"Impuesto: ${detalle['impuesto']:,.2f}\n"
                f"TOTAL: ${detalle['total']:,.2f}\n\n"
                f"Paquete de dos servicios iguales: ${paquete:,.2f}",
            )
            self._informar(f"Cotizacion generada para {identificador}.")

    def _pedir_entero(self, mensaje):
        from tkinter import simpledialog

        valor = simpledialog.askstring("Dato requerido", mensaje, parent=self)
        if valor is None:
            return None
        return valor  # la validacion la hacen las clases del modelo

    # =========================== RESERVAS ===========================
    def _construir_pestana_reservas(self):
        pestana = tk.Frame(self.cuaderno)
        self.cuaderno.add(pestana, text="Reservas")

        formulario = tk.LabelFrame(pestana, text="Nueva reserva", padx=8, pady=8)
        formulario.pack(fill="x", padx=8, pady=8)

        tk.Label(formulario, text="Cliente:").grid(row=0, column=0, sticky="e", padx=5, pady=4)
        self.res_cliente = ttk.Combobox(formulario, state="readonly", width=38)
        self.res_cliente.grid(row=0, column=1, sticky="w", padx=5, pady=4)

        tk.Label(formulario, text="Servicio:").grid(row=1, column=0, sticky="e", padx=5, pady=4)
        self.res_servicio = ttk.Combobox(formulario, state="readonly", width=38)
        self.res_servicio.grid(row=1, column=1, sticky="w", padx=5, pady=4)

        self.res_duracion = self._campo(formulario, "Duracion:", 0, 2, ancho=12)
        self.res_descuento = tk.BooleanVar(value=True)
        tk.Checkbutton(
            formulario,
            text="Aplicar descuento por categoria",
            variable=self.res_descuento,
        ).grid(row=1, column=2, columnspan=2, sticky="w", padx=5, pady=4)

        tk.Button(
            formulario, text="Crear reserva", width=18, command=self.accion_crear_reserva
        ).grid(row=2, column=1, sticky="w", padx=5, pady=4)

        self.tabla_reservas = self._crear_tabla(
            pestana,
            ("ID", "Cliente", "Servicio", "Duracion", "Estado", "Total"),
            (70, 180, 220, 90, 110, 120),
        )

        botones = tk.Frame(pestana)
        botones.pack(fill="x", padx=8, pady=(0, 8))
        tk.Button(botones, text="Confirmar", width=14, command=self.accion_confirmar).pack(
            side="left", padx=4
        )
        tk.Button(botones, text="Procesar", width=14, command=self.accion_procesar).pack(
            side="left", padx=4
        )
        tk.Button(botones, text="Cancelar", width=14, command=self.accion_cancelar).pack(
            side="left", padx=4
        )
        tk.Button(botones, text="Ver detalle", width=14, command=self.accion_detalle).pack(
            side="left", padx=4
        )

    def accion_crear_reserva(self):
        try:
            id_cliente = self.res_cliente.get().split(" - ")[0]
            id_servicio = self.res_servicio.get().split(" - ")[0]
            reserva = self.sistema.crear_reserva(
                id_cliente,
                id_servicio,
                self.res_duracion.get(),
                self.res_descuento.get(),
            )
        except ErrorSistemaFJ as exc:
            self._manejar_error("No fue posible crear la reserva", exc)
        else:
            self.res_duracion.delete(0, tk.END)
            self._informar(f"Reserva {reserva.identificador} creada en estado {reserva.estado}.")
            self.refrescar_todo()

    def _reserva_seleccionada(self):
        seleccion = self.tabla_reservas.selection()
        if not seleccion:
            messagebox.showinfo("Seleccion requerida", "Seleccione una reserva de la tabla.")
            return None
        return self.tabla_reservas.item(seleccion[0], "values")[0]

    def accion_confirmar(self):
        identificador = self._reserva_seleccionada()
        if not identificador:
            return
        try:
            estado = self.sistema.confirmar_reserva(identificador)
        except ErrorSistemaFJ as exc:
            self._manejar_error("No fue posible confirmar la reserva", exc)
        else:
            self._informar(f"Reserva {identificador}: {estado}.")
            self.refrescar_todo()

    def accion_procesar(self):
        identificador = self._reserva_seleccionada()
        if not identificador:
            return
        try:
            total = self.sistema.procesar_reserva(identificador)
        except ErrorSistemaFJ as exc:
            self._manejar_error("No fue posible procesar la reserva", exc)
        else:
            messagebox.showinfo(
                "Reserva procesada", f"Reserva {identificador} liquidada por ${total:,.2f}"
            )
            self._informar(f"Reserva {identificador} procesada por ${total:,.2f}.")
            self.refrescar_todo()

    def accion_cancelar(self):
        identificador = self._reserva_seleccionada()
        if not identificador:
            return
        try:
            self.sistema.cancelar_reserva(identificador, "Cancelada desde la interfaz")
        except ErrorSistemaFJ as exc:
            self._manejar_error("No fue posible cancelar la reserva", exc)
        else:
            self._informar(f"Reserva {identificador} cancelada.")
            self.refrescar_todo()

    def accion_detalle(self):
        identificador = self._reserva_seleccionada()
        if not identificador:
            return
        try:
            reserva = self.sistema.buscar_reserva(identificador)
            cotizacion = reserva.cotizacion()
        except ErrorSistemaFJ as exc:
            self._manejar_error("No fue posible obtener el detalle", exc)
        else:
            observaciones = "\n".join(reserva.observaciones) or "Sin observaciones."
            messagebox.showinfo(
                f"Detalle de {identificador}",
                f"{reserva.describir()}\n\n"
                f"Subtotal: ${cotizacion['subtotal']:,.2f}\n"
                f"Descuento: ${cotizacion['descuento']:,.2f}\n"
                f"Impuesto: ${cotizacion['impuesto']:,.2f}\n"
                f"Total estimado: ${cotizacion['total']:,.2f}\n\n"
                f"Historial:\n{observaciones}",
            )

    # =========================== BITACORA ===========================
    def _construir_pestana_bitacora(self):
        pestana = tk.Frame(self.cuaderno)
        self.cuaderno.add(pestana, text="Bitacora y simulacion")

        botones = tk.Frame(pestana)
        botones.pack(fill="x", padx=8, pady=8)
        tk.Button(
            botones, text="Ejecutar simulacion (18 operaciones)", command=self.accion_simular
        ).pack(side="left", padx=4)
        tk.Button(botones, text="Ver archivo de logs", command=self.accion_ver_logs).pack(
            side="left", padx=4
        )
        tk.Button(botones, text="Ver estadisticas", command=self.accion_estadisticas).pack(
            side="left", padx=4
        )

        contenedor = tk.Frame(pestana)
        contenedor.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.texto_bitacora = tk.Text(contenedor, wrap="none", font=("Consolas", 9))
        barra = ttk.Scrollbar(contenedor, orient="vertical", command=self.texto_bitacora.yview)
        self.texto_bitacora.configure(yscroll=barra.set)
        self.texto_bitacora.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

    def _mostrar_texto(self, contenido):
        self.texto_bitacora.delete("1.0", tk.END)
        self.texto_bitacora.insert("1.0", contenido)

    def accion_simular(self):
        try:
            _, reporte = ejecutar_simulacion(self.sistema)
        except Exception as exc:  # red de seguridad: la ventana nunca debe caerse
            registrar_error("[GUI] Fallo inesperado en la simulacion", exc)
            messagebox.showerror("Simulacion", f"Error inesperado: {exc}")
        else:
            self._mostrar_texto(reporte)
            self._informar("Simulacion ejecutada. Revise el reporte y el archivo de logs.")
            self.refrescar_todo()

    def accion_ver_logs(self):
        self._mostrar_texto(leer_bitacora())
        self._informar("Bitacora cargada desde logs/sistema_fj.log.")

    def accion_estadisticas(self):
        datos = self.sistema.estadisticas()
        catalogo = "\n".join(self.sistema.catalogo()) or "Sin servicios registrados."
        self._mostrar_texto(
            "ESTADISTICAS DEL SISTEMA\n"
            f"  Clientes registrados : {datos['clientes']}\n"
            f"  Servicios creados    : {datos['servicios']}\n"
            f"  Reservas totales     : {datos['reservas']}\n"
            f"  Reservas procesadas  : {datos['procesadas']}\n"
            f"  Reservas canceladas  : {datos['canceladas']}\n"
            f"  Total facturado      : ${datos['facturado']:,.2f}\n\n"
            "CATALOGO DE SERVICIOS (descripciones polimorficas)\n" + catalogo
        )
        self._informar("Estadisticas actualizadas.")

    # =========================== REFRESCO ===========================
    def refrescar_todo(self):
        self._refrescar_clientes()
        self._refrescar_servicios()
        self._refrescar_reservas()
        self._refrescar_combos()

    def _refrescar_clientes(self):
        self.tabla_clientes.delete(*self.tabla_clientes.get_children())
        for cliente in self.sistema.clientes:
            self.tabla_clientes.insert(
                "",
                "end",
                values=(
                    cliente.identificador,
                    cliente.nombre,
                    cliente.documento,
                    cliente.email,
                    cliente.telefono,
                    cliente.categoria,
                    len(cliente.historial),
                ),
            )

    def _refrescar_servicios(self):
        self.tabla_servicios.delete(*self.tabla_servicios.get_children())
        for servicio in self.sistema.servicios:
            self.tabla_servicios.insert(
                "",
                "end",
                values=(
                    servicio.identificador,
                    type(servicio).__name__,
                    servicio.nombre,
                    f"${servicio.costo_base:,.2f}",
                    servicio.unidad,
                    "Disponible" if servicio.disponible else "No disponible",
                    servicio.describir(),
                ),
            )

    def _refrescar_reservas(self):
        self.tabla_reservas.delete(*self.tabla_reservas.get_children())
        for reserva in self.sistema.reservas:
            self.tabla_reservas.insert(
                "",
                "end",
                values=(
                    reserva.identificador,
                    reserva.cliente.nombre,
                    reserva.servicio.nombre,
                    f"{reserva.duracion} {reserva.servicio.unidad}(s)",
                    reserva.estado,
                    f"${reserva.costo_total:,.2f}",
                ),
            )

    def _refrescar_combos(self):
        clientes = [f"{c.identificador} - {c.nombre}" for c in self.sistema.clientes]
        servicios = [f"{s.identificador} - {s.nombre}" for s in self.sistema.servicios]
        self.res_cliente.config(values=clientes)
        self.res_servicio.config(values=servicios)
        if clientes and not self.res_cliente.get():
            self.res_cliente.current(0)
        if servicios and not self.res_servicio.get():
            self.res_servicio.current(0)
