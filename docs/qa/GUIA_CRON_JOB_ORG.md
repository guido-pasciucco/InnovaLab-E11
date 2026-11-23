# Guía: mantener despierta la API con cron-job.org

El servidor gratuito de Render se duerme cuando nadie lo usa, y por eso la primera búsqueda tarda. Para evitarlo, cron-job.org visita la API cada 10 minutos.

> Los nombres de los botones pueden variar un poco según la versión de cron-job.org.

## Crear la tarea (con la cuenta ya creada e iniciada)

- [ ] 1. En el panel (**Dashboard**), tocar **Create cronjob**.
- [ ] 2. Completar la pestaña **Common**:
  - **Title:** `ConCo - mantener despierta la API`
  - **URL:** `https://conco-api.onrender.com/health`
  - **Execution schedule:** **Every 10 minutes**. Si no aparece el 10, elegir **Custom** y escribir `*/10 * * * *`.
- [ ] 3. Opcional: en **Notifications**, activar el aviso por mail cuando falle.
- [ ] 4. En la pestaña **Advanced**, dejar **Request method** en `GET`. El resto queda como viene.
- [ ] 5. Si aparece **Test run**, usarlo para probar. Tiene que dar `200 OK` y la respuesta `{"status":"ok"}`.
- [ ] 6. Tocar **Create** o **Save**.

## Verificar que funciona

- [ ] Después de 20 a 30 minutos, el historial del trabajo (**History**) muestra ejecuciones como *Successful*.
- [ ] En Render, el servicio figura como *Live*.
- [ ] Al día siguiente sigue como *Live*.
- [ ] En Render (*Billing → Monthly Included Usage*), no hay otro servicio gratis despierto todo el mes. Un servicio despierto todo el mes usa unas 730 de las 750 horas gratis.

## Medir la primera búsqueda

Después de que la tarea esté andando, correr dos veces seguidas:

```bash
curl -s -o /dev/null -w "%{time_total}\n" "https://conco-api.onrender.com/guidance/activities?query=peluqueria"
```

- Primera medición: ______ segundos
- Segunda medición: ______ segundos
- Número acordado como aceptable para la primera búsqueda: ______ segundos

## Cuidados

- La dirección siempre es `/health`, nunca una búsqueda: las búsquedas consultan servicios externos.
- Si Render estaba dormido, la primera visita puede tardar o fallar por tiempo de espera. Si el **Test run** falla una vez, volver a probar.

Contexto completo en [NOTAS_DE_IMPLEMENTACION.md](NOTAS_DE_IMPLEMENTACION.md), sección 2.
