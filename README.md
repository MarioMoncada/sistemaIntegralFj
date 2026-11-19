# Sistema Integral de Gestión de Clientes, Servicios y Reservas — Software FJ

Aplicación de escritorio en Python (tkinter) orientada a objetos, **sin bases de datos**:
toda la información vive en objetos y listas en memoria, y los archivos se usan
únicamente para la bitácora de eventos y errores (`logs/sistema_fj.log`).

## Ejecución

```bash
python main.py            # interfaz gráfica (tkinter)
python main.py --consola  # solo la simulación por consola
python simulacion.py      # equivalente a --consola
```

Requiere Python 3.8 o superior. No usa librerías externas.

## Estructura del proyecto

```
sistemaIntegralFj/
├── main.py                        Punto de entrada
├── simulacion.py                  18 operaciones válidas e inválidas
├── excepciones/
│   └── errores.py                 Excepciones personalizadas
├── utilidades/
│   └── registro.py                Bitácora (archivo de logs)
├── modelo/
│   ├── entidad.py                 Clase abstracta EntidadBase
│   ├── cliente.py                 Cliente (encapsulación + validaciones)
│   ├── servicio.py                Clase abstracta Servicio + sobrecargas
│   ├── servicio_sala.py           Reserva de salas (cobro por hora)
│   ├── servicio_equipo.py         Alquiler de equipos (cobro por día)
│   ├── servicio_asesoria.py       Asesorías especializadas (por hora y nivel)
│   └── reserva.py                 Reserva (cliente + servicio + estado)
├── gestion/
│   └── sistema.py                 SistemaFJ: listas internas y operaciones
├── interfaz/
│   └── ventana.py                 Interfaz gráfica tkinter
└── logs/sistema_fj.log            Se crea automáticamente
```

## Cómo se cumple cada requisito

| Requisito | Dónde está |
|---|---|
| Clase abstracta general | `modelo/entidad.py` → `EntidadBase(ABC)` con `describir()` y `validar()` abstractos |
| Clase `Cliente` con validaciones y encapsulación | `modelo/cliente.py`: atributos `_privados` expuestos con `@property`/setters que validan nombre, documento, correo, teléfono y categoría |
| Clase abstracta `Servicio` + 3 especializaciones | `modelo/servicio.py` y los tres servicios: `ServicioSala`, `ServicioEquipo`, `ServicioAsesoria` |
| Polimorfismo / métodos sobrescritos | Cada servicio sobrescribe `calcular_costo()`, `validar_parametros()` y `describir()`; `SistemaFJ.catalogo()` los recorre de forma uniforme |
| Herencia | `Cliente`, `Servicio` y `Reserva` heredan de `EntidadBase`; los tres servicios heredan de `Servicio` |
| Métodos sobrecargados | `Servicio.calcular_total(duracion, impuesto, descuento, extras)` (parámetros opcionales) y `Servicio.cotizar()` con `singledispatchmethod` para `int`, `float`, `list`/`tuple` y `dict` |
| Clase `Reserva` con estado | `modelo/reserva.py`: estados `PENDIENTE → CONFIRMADA → PROCESADA` o `CANCELADA`, con `confirmar()`, `cancelar()` y `procesar()` |
| Excepciones personalizadas | `excepciones/errores.py`: 8 clases derivadas de `ErrorSistemaFJ` |
| `try/except`, `try/except/else`, `try/except/finally` | `SistemaFJ.registrar_cliente()` (else + finally), `Reserva.procesar()` (except + else + finally), `Reserva.confirmar()` (except + else) |
| Encadenamiento de excepciones | `raise ErrorValidacion(...) from exc` en los setters y `raise ErrorReservaInvalida(...) from exc` en `Reserva.validar()`; la bitácora y los diálogos muestran la causa original |
| Archivo de logs | `utilidades/registro.py` escribe eventos, advertencias y errores en `logs/sistema_fj.log` |
| 10+ operaciones simuladas | `simulacion.py`: 18 operaciones (clientes válidos/inválidos, servicios correctos/incorrectos, reservas exitosas y fallidas, cálculos sobrecargados) |
| El sistema nunca se cae | Todas las acciones de la interfaz pasan por `try/except` y `_manejar_error()`; `main.py` tiene una red de seguridad final |

## Reglas de negocio

- **Salas**: cobro por hora, 1 a 12 horas; recargo del 15 % si la capacidad supera 20 personas
  (y máximo 8 horas continuas en esas salas).
- **Equipos**: cobro por día y por unidad, 1 a 30 días, más un depósito de garantía del 10 %
  (máximo 15 días cuando se alquilan más de 20 equipos).
- **Asesorías**: cobro por hora, 1 a 8 horas, multiplicado por el nivel del consultor
  (junior ×1.0, senior ×1.4, experto ×1.8; el experto exige mínimo 2 horas).
- **Descuentos por categoría de cliente**: regular 0 %, premium 10 %, corporativo 15 %.
- **IVA** por defecto: 19 % (configurable en cada cálculo).

## Uso de la interfaz

1. **Clientes**: llene el formulario y pulse *Registrar cliente*. Los datos inválidos
   muestran el error y quedan en la bitácora, sin cerrar la aplicación.
2. **Servicios**: elija el tipo (los campos adicionales cambian solos), cree el servicio,
   actívelo/desactívelo o cotícelo.
3. **Reservas**: seleccione cliente y servicio, indique la duración y use
   *Confirmar*, *Procesar*, *Cancelar* o *Ver detalle*.
4. **Bitácora y simulación**: ejecuta las 18 operaciones de prueba, muestra el archivo
   de logs y las estadísticas del sistema.
