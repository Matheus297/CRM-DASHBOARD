import asyncio
import logging
import os
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

# WhatsApp Web URL
WHATSAPP_WEB_URL = "https://web.whatsapp.com/"

# Configuração de tempo de espera
MAX_WAIT_TIME = 90000  # 90 segundos - aumentado para ambientes de baixo processamento

# Caminho para salvar o estado da sessão do navegador
SESSION_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sessions')
os.makedirs(SESSION_DIR, exist_ok=True)

async def init_browser():
    """Inicializa o navegador em modo headless para automação."""
    try:
        # Em ambientes como Replit, precisamos usar configurações específicas
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=True,  # Sempre usar headless em ambientes como Replit
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-infobars',
                '--window-position=0,0',
                '--ignore-certificate-errors',
                '--ignore-certificate-errors-spki-list',
                '--mute-audio',
                '--disable-extensions',
                '--disable-default-apps',
                '--enable-features=NetworkService',
                '--disable-features=TranslateUI',
                '--disable-notifications',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-breakpad',
                '--disable-component-extensions-with-background-pages',
                '--disable-ipc-flooding-protection',
                '--disable-renderer-backgrounding',
            ],
            # Aumentando o timeout para lançamento
            timeout=60000,
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        
        # Cria uma nova página
        page = await context.new_page()
        
        return playwright, browser, context, page
    except Exception as e:
        logger.error(f"Erro ao inicializar o navegador: {str(e)}")
        # Repassar a exceção para que o chamador possa lidar com ela
        raise

async def load_whatsapp_web(page):
    """Carrega o WhatsApp Web e aguarda pelo QR code."""
    try:
        # Aumentando o timeout para carregar a página
        await page.goto(WHATSAPP_WEB_URL, wait_until="networkidle", timeout=90000)
        
        # Aguardar que a página carregue completamente
        await asyncio.sleep(3)
        
        # Verifica se o QR code está visível
        qr_code = await page.query_selector('[data-testid="qrcode"]')
        
        if qr_code:
            logger.info("Por favor, escaneie o código QR no navegador para continuar.")
            
            # Em um ambiente real, aqui capturaríamos a imagem do QR code
            # para exibir na interface, mas isso não é possível no ambiente Replit
            
            return False
        else:
            # Verifica se já está logado (procura por seletores típicos da página principal)
            chat_list = await page.query_selector('[data-testid="chat-list"]')
            compose_box = await page.query_selector('[data-testid="conversation-compose-box"]')
            
            if chat_list or compose_box:
                logger.info("WhatsApp Web já está logado e pronto para uso.")
                return True
            else:
                logger.info("WhatsApp Web carregado, mas não foi possível detectar o estado de login.")
                return False
            
    except Exception as e:
        logger.error(f"Erro ao carregar WhatsApp Web: {str(e)}")
        return False

async def send_whatsapp_message(phone_number, message):
    """Envia uma mensagem para um número específico no WhatsApp Web."""
    playwright = None
    browser = None
    
    try:
        # Inicializa um navegador com as configurações para ambiente Replit
        playwright, browser, context, page = await init_browser()
        
        # Carrega o WhatsApp Web
        success = await load_whatsapp_web(page)
        if not success:
            logger.error("Não foi possível carregar o WhatsApp Web. Verifique se você escaneou o QR code.")
            await cleanup(playwright, browser)
            return False
        
        # Formata o número do telefone (remove caracteres não numéricos)
        clean_phone = ''.join(c for c in phone_number if c.isdigit())
        
        # Se o número não começar com +, adicionar o código do país (Brasil +55)
        if not clean_phone.startswith('55'):
            clean_phone = '55' + clean_phone
        
        # Validação básica do número
        if len(clean_phone) < 10:
            logger.warning(f"Número de telefone inválido: {phone_number}")
            await cleanup(playwright, browser)
            return False
        
        # Gera o URL direto para o chat
        direct_chat_url = f"{WHATSAPP_WEB_URL}send?phone={clean_phone}&text={message}"
        
        # Navega para o URL de chat direto com timeout aumentado
        await page.goto(direct_chat_url, wait_until="networkidle", timeout=60000)
        
        # Verifica se há um erro com o número de telefone (indicado pelo WhatsApp)
        error_selector = 'div._9a59P'
        error_element = await page.query_selector(error_selector)
        
        if error_element:
            error_text = await error_element.text_content()
            logger.warning(f"Erro do WhatsApp para {phone_number}: {error_text}")
            await cleanup(playwright, browser)
            return False
        
        # Aguarda o carregamento da interface de chat
        await page.wait_for_selector('[data-testid="conversation-compose-box-input"]', timeout=MAX_WAIT_TIME)
        
        # Clica no botão de enviar
        send_button = await page.wait_for_selector('[data-testid="compose-btn-send"]', timeout=10000)
        if send_button:
            await send_button.click()
            logger.info(f"Mensagem enviada com sucesso para {phone_number}")
            await asyncio.sleep(2)  # Pequena pausa para garantir que a mensagem foi enviada
            await cleanup(playwright, browser)
            return True
        else:
            logger.error(f"Botão de enviar não encontrado para {phone_number}")
            await cleanup(playwright, browser)
            return False
            
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem via WhatsApp Web: {str(e)}")
        try:
            if playwright and browser:
                await cleanup(playwright, browser)
        except Exception as cleanup_error:
            logger.error(f"Erro adicional durante cleanup: {str(cleanup_error)}")
        return False

async def send_bulk_messages(recipients, message_template):
    """Envia mensagens em massa para vários destinatários.
    
    Args:
        recipients (list): Lista de dicionários com 'phone' e 'name' dos destinatários
        message_template (str): Modelo de mensagem com placeholders como {nome}
        
    Returns:
        dict: Resultado do envio com sucessos e falhas
    """
    results = {
        'total': len(recipients),
        'success': 0,
        'failed': 0,
        'failed_recipients': [],
        'error_message': None
    }
    
    playwright = None
    browser = None
    
    try:
        # Inicializa o navegador
        playwright, browser, context, page = await init_browser()
        
        # Carrega o WhatsApp Web
        success = await load_whatsapp_web(page)
        if not success:
            error_msg = "Não foi possível carregar o WhatsApp Web. Verifique se você escaneou o QR code."
            logger.error(error_msg)
            results['error_message'] = error_msg
            await cleanup(playwright, browser)
            return results
        
        # Processa cada destinatário
        for i, recipient in enumerate(recipients):
            try:
                # Personaliza a mensagem
                personalized_message = message_template
                if '{nome}' in message_template and 'name' in recipient and recipient['name']:
                    personalized_message = message_template.replace('{nome}', recipient['name'])
                
                # Formata o número do telefone
                phone = recipient['phone']
                clean_phone = ''.join(c for c in phone if c.isdigit())
                if not clean_phone.startswith('55'):
                    clean_phone = '55' + clean_phone
                
                # Validação básica do número de telefone
                if len(clean_phone) < 10:
                    logger.warning(f"Número de telefone inválido: {phone}")
                    results['failed'] += 1
                    results['failed_recipients'].append({
                        'phone': phone,
                        'name': recipient.get('name', ''),
                        'reason': 'Número de telefone inválido'
                    })
                    continue
                
                # Gera o URL direto para o chat
                direct_chat_url = f"{WHATSAPP_WEB_URL}send?phone={clean_phone}&text={personalized_message}"
                
                # Navega para o URL de chat direto com timeout aumentado
                await page.goto(direct_chat_url, wait_until="networkidle", timeout=90000)
                
                # Verifica se há um erro com o número de telefone (indicado pelo WhatsApp)
                error_selector = 'div._9a59P'
                error_element = await page.query_selector(error_selector)
                
                if error_element:
                    error_text = await error_element.text_content()
                    logger.warning(f"Erro do WhatsApp para {phone}: {error_text}")
                    results['failed'] += 1
                    results['failed_recipients'].append({
                        'phone': phone,
                        'name': recipient.get('name', ''),
                        'reason': error_text
                    })
                    continue
                
                # Aguarda o carregamento da interface de chat
                input_field = await page.wait_for_selector('[data-testid="conversation-compose-box-input"]', timeout=MAX_WAIT_TIME)
                
                # Verifica se há um botão de enviar
                send_button = await page.query_selector('[data-testid="compose-btn-send"]')
                if send_button:
                    await send_button.click()
                    logger.info(f"Mensagem enviada com sucesso para {phone}")
                    results['success'] += 1
                    
                    # Intervalo de 5 segundos entre mensagens para evitar bloqueio
                    # Mais tempo para envios mais confiáveis
                    await asyncio.sleep(5)
                else:
                    logger.error(f"Botão de enviar não encontrado para {phone}")
                    results['failed'] += 1
                    results['failed_recipients'].append({
                        'phone': phone,
                        'name': recipient.get('name', ''),
                        'reason': 'Botão de envio não encontrado'
                    })
                    
            except Exception as e:
                error_msg = f"Erro ao enviar mensagem para {recipient['phone']}: {str(e)}"
                logger.error(error_msg)
                results['failed'] += 1
                results['failed_recipients'].append({
                    'phone': recipient.get('phone', 'desconhecido'),
                    'name': recipient.get('name', ''),
                    'reason': str(e)
                })
        
        # Encerra o navegador
        await cleanup(playwright, browser)
        return results
        
    except Exception as e:
        error_msg = f"Erro ao iniciar envio em massa: {str(e)}"
        logger.error(error_msg)
        results['error_message'] = error_msg
        
        try:
            if playwright and browser:
                await cleanup(playwright, browser)
        except Exception as cleanup_error:
            logger.error(f"Erro adicional durante cleanup: {str(cleanup_error)}")
            
        return results

async def cleanup(playwright, browser):
    """Fecha o navegador e encerra o Playwright."""
    try:
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()
    except Exception as e:
        logger.error(f"Erro ao limpar recursos: {str(e)}")

# Função auxiliar para execução síncrona
def send_message_sync(phone_number, message):
    """Versão síncrona da função de envio de mensagem para compatibilidade com código existente."""
    return asyncio.run(send_whatsapp_message(phone_number, message))

# Função auxiliar para envio em massa síncrono
def send_bulk_messages_sync(recipients, message_template):
    """Versão síncrona da função de envio em massa para compatibilidade com código existente."""
    return asyncio.run(send_bulk_messages(recipients, message_template))
