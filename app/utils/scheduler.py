import os
import threading
import time
import datetime

def habilitar_semanas_online(motivo):
    """
    Habilita las semanas online pagadas por adelantado cuya fecha ya llegó y reintenta las que fallaron en Moodle.
    Las semanas inician en sábado, así que la corrida de los sábados 07:00 es la que libera semanas nuevas; las
    demás corridas (diaria y al arrancar la API) solo recuperan lo pendiente si la API estuvo apagada o Moodle falló.
    """
    try:
        from app.services.online_service import OnlineService
        resultado, _ = OnlineService.habilitar_pendientes()
        print(f"[Scheduler] Semanas online ({motivo}): {resultado.get('semanas_habilitadas', 0)} habilitadas, "
              f"{len(resultado.get('con_error', []))} alumnos con error de Moodle")
    except Exception as e:
        print(f"[Scheduler] Error habilitando semanas online: {e}")


def iniciar_scheduler(app):
    def job():
        # Espera inicial para dar tiempo a que se configure el servidor Flask
        time.sleep(10)
        habilitar_semanas_online("al iniciar la API")

        while True:
            ahora = datetime.datetime.now()
            # Calcular la próxima corrida a las 7:00 AM
            proxima_corrida = ahora.replace(hour=7, minute=0, second=0, microsecond=0)
            
            # Si ya pasó de las 7:00 AM hoy, se programa para mañana
            if ahora >= proxima_corrida:
                proxima_corrida += datetime.timedelta(days=1)
                
            segundos_espera = (proxima_corrida - ahora).total_seconds()
            print(f"[Scheduler] Próxima actualización programada para las 7:00 AM del {proxima_corrida.strftime('%Y-%m-%d %H:%M:%S')} (en {segundos_espera:.1f} segundos)")
            
            # Dormir en intervalos cortos para mayor control
            while segundos_espera > 0:
                sleep_time = min(segundos_espera, 60)
                time.sleep(sleep_time)
                segundos_espera -= sleep_time
                
            # Ejecutar actualización
            try:
                print("[Scheduler] Iniciando actualización diaria de niveles académicos de grupos...")
                from app.services.periodos_academico import PeriodoAcademicoService
                actualizados = PeriodoAcademicoService.actualizarTodosLosGrupos()
                print(f"[Scheduler] Proceso completado. Grupos actualizados: {actualizados}")
            except Exception as e:
                print(f"[Scheduler] Error durante la actualización de niveles: {e}")

            habilitar_semanas_online("sábado 07:00" if datetime.datetime.now().weekday() == 5 else "revisión diaria 07:00")

    # En modo de depuración, Flask ejecuta dos procesos. Solo levantamos el scheduler en el proceso principal.
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        print("[Scheduler] Registrando hilo de actualización diaria de grupos (7:00 AM)")
        thread = threading.Thread(target=job, daemon=True)
        thread.start()
