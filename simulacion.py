"""
Simulacion de operaciones del sistema Software FJ.

Ejecuta mas de 10 operaciones completas (validas e invalidas) para
demostrar que la aplicacion sigue funcionando ante errores graves.
Puede ejecutarse sola (python simulacion.py) o desde la interfaz grafica.
"""
from excepciones.errores import ErrorSistemaFJ
from gestion.sistema import SistemaFJ
from utilidades.registro import registrar_error, registrar_evento


class _Bitacora:
    """Acumula el resultado de cada operacion para mostrarlo en pantalla."""

    def __init__(self):
        self.lineas = []
        self._numero = 0

    def ok(self, titulo, detalle):
        self._numero += 1
        self.lineas.append(f"OP {self._numero:02d} [OK]    {titulo}\n            {detalle}")
        registrar_evento(f"SIMULACION OP{self._numero:02d} OK - {titulo}: {detalle}")

    def fallo(self, titulo, excepcion):
        self._numero += 1
        causa = excepcion.__cause__
        texto = f"{type(excepcion).__name__}: {excepcion}"
        if causa is not None:
            texto += f"\n            causa original -> {type(causa).__name__}: {causa}"
        self.lineas.append(f"OP {self._numero:02d} [ERROR] {titulo}\n            {texto}")
        registrar_error(f"SIMULACION OP{self._numero:02d} - {titulo}", excepcion)

    def texto(self):
        return "\n".join(self.lineas)


def ejecutar_simulacion(sistema=None):
    """
    Corre la bateria de operaciones sobre el sistema recibido
    (o sobre uno nuevo) y devuelve (sistema, texto_del_reporte).
    """
    sistema = sistema or SistemaFJ()
    log = _Bitacora()
    registrar_evento("--- Inicio de la simulacion de operaciones ---")

    # 1. Cliente valido
    try:
        cliente1 = sistema.registrar_cliente(
            "Laura Gomez", "1098765432", "laura.gomez@correo.com", "3001234567", "premium"
        )
    except ErrorSistemaFJ as exc:
        cliente1 = None
        log.fallo("Registro de cliente valido", exc)
    else:
        log.ok("Registro de cliente valido", cliente1.resumen())

    # 2. Segundo cliente valido (corporativo)
    try:
        cliente2 = sistema.registrar_cliente(
            "Carlos Rincon", "800123456", "carlos@empresa.com", "6017654321", "corporativo"
        )
    except ErrorSistemaFJ as exc:
        cliente2 = None
        log.fallo("Registro de cliente corporativo", exc)
    else:
        log.ok("Registro de cliente corporativo", cliente2.resumen())

    # 3. Cliente invalido: correo mal formado
    try:
        sistema.registrar_cliente("Ana Torres", "1012223334", "ana#correo", "3109998877")
    except ErrorSistemaFJ as exc:
        log.fallo("Registro invalido (correo mal formado)", exc)
    else:
        log.ok("Registro invalido (correo mal formado)", "No deberia haberse aceptado")

    # 4. Cliente invalido: documento no numerico
    try:
        sistema.registrar_cliente("Pedro Ruiz", "ABC123", "pedro@correo.com", "3001112222")
    except ErrorSistemaFJ as exc:
        log.fallo("Registro invalido (documento no numerico)", exc)
    else:
        log.ok("Registro invalido (documento no numerico)", "No deberia haberse aceptado")

    # 5. Cliente duplicado
    try:
        sistema.registrar_cliente(
            "Laura Gomez Duplicada", "1098765432", "otro@correo.com", "3005554444"
        )
    except ErrorSistemaFJ as exc:
        log.fallo("Registro duplicado de documento", exc)
    else:
        log.ok("Registro duplicado de documento", "No deberia haberse aceptado")

    # 6. Servicio de sala valido
    try:
        sala = sistema.registrar_servicio("sala", "Sala Innovacion", 60000, 25, "Piso 3")
    except ErrorSistemaFJ as exc:
        sala = None
        log.fallo("Creacion de servicio de sala", exc)
    else:
        log.ok("Creacion de servicio de sala", sala.resumen())

    # 7. Servicio de equipos valido
    try:
        equipos = sistema.registrar_servicio("equipo", "Portatiles Dell", 35000, 10, "computo")
    except ErrorSistemaFJ as exc:
        equipos = None
        log.fallo("Creacion de servicio de equipos", exc)
    else:
        log.ok("Creacion de servicio de equipos", equipos.resumen())

    # 8. Servicio de asesoria valido
    try:
        asesoria = sistema.registrar_servicio(
            "asesoria", "Asesoria en Ciberseguridad", 120000, "Ciberseguridad", "experto"
        )
    except ErrorSistemaFJ as exc:
        asesoria = None
        log.fallo("Creacion de servicio de asesoria", exc)
    else:
        log.ok("Creacion de servicio de asesoria", asesoria.resumen())

    # 9. Servicio invalido: costo base negativo
    try:
        sistema.registrar_servicio("sala", "Sala Economica", -5000, 10)
    except ErrorSistemaFJ as exc:
        log.fallo("Creacion invalida (costo negativo)", exc)
    else:
        log.ok("Creacion invalida (costo negativo)", "No deberia haberse aceptado")

    # 10. Servicio invalido: tipo inexistente / parametro faltante
    try:
        sistema.registrar_servicio("catering", "Refrigerios", 15000, 20)
    except ErrorSistemaFJ as exc:
        log.fallo("Creacion invalida (tipo no soportado)", exc)
    else:
        log.ok("Creacion invalida (tipo no soportado)", "No deberia haberse aceptado")

    # 11. Reserva exitosa: creacion, confirmacion y procesamiento
    if cliente1 and sala:
        try:
            reserva = sistema.crear_reserva(cliente1.identificador, sala.identificador, 4)
            sistema.confirmar_reserva(reserva.identificador)
            total = sistema.procesar_reserva(reserva.identificador)
        except ErrorSistemaFJ as exc:
            log.fallo("Reserva completa de sala", exc)
        else:
            log.ok(
                "Reserva completa de sala",
                f"{reserva.identificador} procesada por ${total:,.2f} "
                f"(descuento cliente {cliente1.descuento_por_categoria():.0%})",
            )

    # 12. Reserva con duracion fuera de rango
    if cliente2 and asesoria:
        try:
            sistema.crear_reserva(cliente2.identificador, asesoria.identificador, 20)
        except ErrorSistemaFJ as exc:
            log.fallo("Reserva invalida (duracion fuera de rango)", exc)
        else:
            log.ok("Reserva invalida (duracion fuera de rango)", "No deberia haberse aceptado")

    # 13. Reserva sobre un servicio no disponible
    if cliente2 and equipos:
        try:
            sistema.alternar_disponibilidad(equipos.identificador)  # se marca no disponible
            sistema.crear_reserva(cliente2.identificador, equipos.identificador, 3)
        except ErrorSistemaFJ as exc:
            log.fallo("Reserva invalida (servicio no disponible)", exc)
        else:
            log.ok("Reserva invalida (servicio no disponible)", "No deberia haberse aceptado")
        finally:
            sistema.alternar_disponibilidad(equipos.identificador)  # se restablece

    # 14. Procesar una reserva que no fue confirmada
    if cliente2 and equipos:
        try:
            pendiente = sistema.crear_reserva(cliente2.identificador, equipos.identificador, 5)
            sistema.procesar_reserva(pendiente.identificador)
        except ErrorSistemaFJ as exc:
            log.fallo("Procesar reserva no confirmada", exc)
        else:
            log.ok("Procesar reserva no confirmada", "No deberia haberse aceptado")

    # 15. Cancelacion valida y segundo intento de cancelacion
    if cliente2 and asesoria:
        try:
            reserva_cancelar = sistema.crear_reserva(
                cliente2.identificador, asesoria.identificador, 3
            )
            sistema.cancelar_reserva(reserva_cancelar.identificador, "Cambio de agenda")
            log.ok(
                "Cancelacion de reserva",
                f"{reserva_cancelar.identificador} quedo en estado {reserva_cancelar.estado}",
            )
            sistema.procesar_reserva(reserva_cancelar.identificador)
        except ErrorSistemaFJ as exc:
            log.fallo("Procesar una reserva cancelada", exc)

    # 16. Metodos sobrecargados de calculo de costos
    if asesoria:
        try:
            sin_impuesto = asesoria.calcular_total(3, impuesto=0.0)
            con_descuento = asesoria.calcular_total(3, descuento=0.15)
            con_extras = asesoria.calcular_total(3, extras={"material": 25000})
            paquete = asesoria.cotizar([2, 3])
            parametrizada = asesoria.cotizar({"duracion": 4, "descuento": 0.1})
        except ErrorSistemaFJ as exc:
            log.fallo("Sobrecarga del calculo de costos", exc)
        else:
            log.ok(
                "Sobrecarga del calculo de costos",
                f"sin IVA ${sin_impuesto:,.2f} | con descuento ${con_descuento:,.2f} | "
                f"con extras ${con_extras:,.2f} | paquete [2,3] ${paquete:,.2f} | "
                f"parametrizada ${parametrizada:,.2f}",
            )

    # 17. Cotizacion con un tipo de dato no soportado
    if sala:
        try:
            sala.cotizar("cuatro horas")
        except ErrorSistemaFJ as exc:
            log.fallo("Cotizacion con tipo de dato invalido", exc)

    # 18. Resumen final del sistema
    datos = sistema.estadisticas()
    log.ok(
        "Resumen del sistema",
        f"clientes {datos['clientes']} | servicios {datos['servicios']} | "
        f"reservas {datos['reservas']} | procesadas {datos['procesadas']} | "
        f"canceladas {datos['canceladas']} | facturado ${datos['facturado']:,.2f}",
    )

    registrar_evento("--- Fin de la simulacion de operaciones ---")
    return sistema, log.texto()


if __name__ == "__main__":
    _, reporte = ejecutar_simulacion()
    print(reporte)
