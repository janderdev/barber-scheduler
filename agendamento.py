import asyncio
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
import os

LAST_FILE = "last_cut.txt"

def proximo_sabado(data_base: datetime) -> datetime:
    """Dado uma data base, retorna o próximo sábado."""
    dias_ate_sabado = (5 - data_base.weekday()) % 7  # 5 = sábado
    if dias_ate_sabado == 0:  # se já é sábado, pula pro próximo
        dias_ate_sabado = 7
    return data_base + timedelta(days=dias_ate_sabado)

async def agendar():
    url = "https://app.pointly.com.br/appointment/company/17c771ad-594c-41d7-92f5-667fcf66a44d"

    nome_cliente = "Jander"
    telefone = "88996776422"
    servico = "Corte 💈❤️"
    profissional = "Digas Barber"
    intervalo = 21  # dias entre cortes

    # Verifica última data registrada
    if os.path.exists(LAST_FILE):
        with open(LAST_FILE, "r") as f:
            last_date = datetime.strptime(f.read().strip(), "%Y-%m-%d").date()
        if datetime.now().date() < (last_date + timedelta(days=intervalo)):
            print("⏭ Ainda não deu 21 dias desde o último corte.")
            return
    else:
        print("⚠ Nenhum histórico encontrado, criando um novo agendamento.")

    # Calcula o próximo sábado válido
    alvo = last_date + timedelta(days=intervalo)
    data_agendamento = proximo_sabado(alvo).strftime("%Y-%m-%d")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)

        # Seleciona serviço e profissional
        await page.click(f"text={servico}")
        await page.click(f"text={profissional}")

        # Seleciona data
        await page.click(f"[aria-label='{data_agendamento}']")

        # Seleciona o primeiro horário >= 12h
        horarios = await page.query_selector_all("button:has-text(':')")
        horario_escolhido = None
        for h in horarios:
            hora_texto = await h.inner_text()
            try:
                hora = datetime.strptime(hora_texto.strip(), "%H:%M").time()
                if hora >= datetime.strptime("12:00", "%H:%M").time():
                    await h.click()
                    horario_escolhido = hora_texto
                    break
            except:
                continue

        if not horario_escolhido:
            print("⚠ Nenhum horário >= 12h encontrado, nada foi marcado.")
            await browser.close()
            return

        # Preenche nome e telefone
        await page.fill("input[placeholder='Nome']", nome_cliente)
        await page.fill("input[placeholder='Celular']", telefone)

        # Confirma agendamento
        await page.click("button:has-text('Confirmar')")

        print(f"✅ Agendamento feito para {data_agendamento} às {horario_escolhido} com {profissional}")
        await browser.close()

    # Atualiza o arquivo com a data do próximo corte real
    with open(LAST_FILE, "w") as f:
        f.write(data_agendamento)

asyncio.run(agendar())
