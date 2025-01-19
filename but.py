import telebot
import random
import threading
import schedule
import time
import html
import mysql.connector

from handlers_ADM import handleEditar, handleConfirmarExlusao, handleEditarAdm, handleEditarFixados, handleEditarMensagens, handleMenuAdm, receber_id_adm, handle_aprova_ou_rejeita, handleListarGrupos
from handlers_User import handleMenu, handleCallMenu
from telebot.types import ChatMemberUpdated
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import datetime
import logging

bot = telebot.TeleBot(token="7729962379:AAFWDwssjjJ2RldSg5TlJGwoHosWcvwWiGQ", parse_mode='HTML')

def conectar_ao_banco():
    try:
        return mysql.connector.connect(
                host="127.0.0.1",
                user="root",
                password="root",
                database="ItsInvictus"
            )
    except mysql.connector.Error as err:
        logging.error(f"Erro de conexão: {err}")
        return None

@bot.message_handler(content_types=['left_chat_member'])
def left_chat_member(message):
    if message.left_chat_member.is_bot:
        chat_id = message.chat.id
        logging.info(f'O bot foi removido do grupo/canal {chat_id}')

        # Conectar ao banco de dados
        conexao = conectar_ao_banco()

        if not conexao:
            logging.error("Não foi possível conectar ao banco de dados.")
            return

        cursor = conexao.cursor()

        try:
            # Verificar se o chat_id existe na tabela Grupo_e_Canal
            cursor.execute("SELECT * FROM grupos_e_canais WHERE id = %s", (chat_id,))
            grupo_canal = cursor.fetchone()

            if grupo_canal:
                # Se o bot foi removido de um grupo/canal registrado, podemos excluir o registro
                cursor.execute("DELETE FROM grupos_e_canais WHERE id = %s", (chat_id,))
                conexao.commit()
                logging.info(f'Grupo/Canal removido do banco: {grupo_canal[1]} (ID: {grupo_canal[0]})')
            else:
                logging.info(f'O grupo/canal com ID {chat_id} não foi encontrado no banco de dados.')

        except mysql.connector.Error as err:
            logging.error(f"Erro ao acessar o banco de dados: {err}")
        finally:
            cursor.close()
            conexao.close()

@bot.message_handler(commands=['start'])
def start(message):

    chat_type = message.chat.type

    if chat_type in ['group', 'supergroup', 'channel']:
        # Ignora o comando em grupos e supergrupos
        print(f"Ignorando /start no grupo: {message.chat.title}")
        return


    else:
        handleMenu(bot, message)

@bot.callback_query_handler(func=lambda call: call.data.startswith('menu'))
def call_menu_user(call):
    handleCallMenu(bot, call)

@bot.message_handler(commands=['1000'])
def Adm(message):
    handleMenuAdm(bot, message)

@bot.callback_query_handler(func=lambda call: call.data.startswith('editar'))
def call_menu(call):
    handleEditar(bot, call)
    handleEditarMensagens(bot, call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('selecionar_'))
def fixados(call):
    handleEditarFixados(bot, call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm'))
def call_me(call):
    handleEditarAdm(bot, call)


@bot.message_handler(commands=['listar_grupos'])
def listar_grupos(message):
    handleListarGrupos(bot, message)

@bot.callback_query_handler(func=lambda call: call.data.startswith('aprovar_') or call.data.startswith('banir_'))
def aprova_ou_rejeita(call):
    handle_aprova_ou_rejeita(bot, call)


# Manipulador de eventos: quando o bot é adicionado ao grupo/canal
@bot.my_chat_member_handler(func=lambda event: event.new_chat_member.user.id == bot.get_me().id)
def handle_new_chat_member(event: ChatMemberUpdated):
    if event.new_chat_member.status in ['member', 'administrator']:
        chat_id = event.chat.id
        try:
            # Conectar ao banco de dados
            connection = conectar_ao_banco()
            if connection is None:
                bot.leave_chat(chat_id)
                return

            cursor = connection.cursor()

            # Verificar se o grupo/canal foi banido
            cursor.execute("SELECT id FROM grupos_e_canais_banidos WHERE id = %s", (chat_id,))
            grupo_banido = cursor.fetchone()

            if grupo_banido:
                print(f"Grupo/Canal {chat_id} está banido. Saindo do grupo.")
                bot.leave_chat(chat_id)
                cursor.close()
                connection.close()
                return

            print(f"Bot adicionado ao chat: {chat_id}")

            user_id = event.from_user.id
            print(f"Usuário que adicionou: {user_id}")

            # Obter quantidade de participantes
            members_count = bot.get_chat_members_count(chat_id)
            print(f"Número de membros: {members_count}")

            if members_count < 150:
                bot.leave_chat(chat_id)
                bot.send_message(user_id, 'Você não tem integrantes suficientes para participar da lista🙁')
                cursor.close()
                connection.close()
                return

            # Tentar pegar o link do grupo
            try:
                link = bot.export_chat_invite_link(chat_id)
            except Exception as e:
                print(f"Erro ao obter link: {e}")
                link = None
                bot.leave_chat(chat_id)
                cursor.close()
                connection.close()
                return

            tipo_chat = event.chat.type
            print(f'\nTipo de chat: {tipo_chat}\n')

            if tipo_chat in ['group', 'supergroup']:
                tipo_chat = 'Grupo'
            elif tipo_chat == 'channel':
                tipo_chat = 'Canal'

            # Verificar se o grupo/canal já existe no banco
            cursor.execute("SELECT id FROM grupos_e_canais WHERE id = %s", (chat_id,))
            existing_group = cursor.fetchone()

            if existing_group:
                print("Grupo/Canal já existe no banco. Nenhuma ação necessária.")
                bot.send_message(chat_id, "O bot já está configurado para este chat.")
                cursor.close()
                connection.close()
                return

            # Adicionar novo grupo/canal ao banco
            cursor.execute(
                """
                INSERT INTO grupos_e_canais (id, nome, id_usuario, link, tipo, apro)
                VALUES (%s, %s, %s, %s, %s, %s)
                """, (chat_id, event.chat.title, user_id, link, tipo_chat, False)
            )

            connection.commit()

            bot.send_message(chat_id, "Bot adicionado e configurado com sucesso!")

        except Exception as e:
            print(f"Erro ao adicionar o bot ao chat {chat_id}: {e}")
            bot.leave_chat(chat_id)
            bot.send_message(event.from_user.id, "Houve um erro ao configurar o bot para o grupo/canal.")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

grupos = {}
grupos_repetidos = {}

# Função para carregar dados
def carregar_dados():
    global grupos
    global grupos_repetidos
    global grupos_fixados
    global mensagem_lista

    # Estabelece a conexão com o banco
    conn = conectar_ao_banco()
    if conn is None:
        print("❌ Não foi possível conectar ao banco de dados.")
        return

    try:
        cursor = conn.cursor()

        # Busca dados no banco de dados para grupos aprovados
        cursor.execute("SELECT id, nome, link FROM grupos_e_canais WHERE apro = True")
        resultados = cursor.fetchall()

        # Consulta para grupos fixados
        cursor.execute("SELECT id, nome, link FROM grupos_e_canais WHERE fixado = True")
        grupos_fixados_resultados = cursor.fetchall()

        # Criação dos dicionários
        grupos = {id: [nome, link] for id, nome, link in resultados}
        grupos_fixados = {id: [nome, link] for id, nome, link in grupos_fixados_resultados}

        cursor.execute("SELECT Mensagem_Lista FROM mensagens LIMIT 1")
        mensagem_lista = cursor.fetchone()

        print("Dados carregados às 5:00.")

    except mysql.connector.Error as err:
        print(f"Erro ao consultar o banco de dados: {err}")

    finally:
        # Fecha a conexão com o banco de dados
        conn.close()




# Função para monitorar e enviar a lista de grupos
def primeira_lista():
    global grupos
    global grupos_fixados
    global mensagem_lista

    if not grupos:
        print("❌ A lista de grupos está vazia. Carregue os dados antes de chamar essa função.")
        return
    conn = conectar_ao_banco()
    if conn is None:
        print("❌ Não foi possível conectar ao banco de dados.")
        return

    cursor = conn.cursor()
    i = 0

    for grupo_id in grupos.keys():
        i += 1
        if i == 10:
            time.sleep(5)
            i = 0
        try:
            # Seleciona 20 grupos aleatoriamente
            chaves_aleatorias = random.sample(list(grupos.keys()), min(30, len(grupos)))
            grupos_selecionados = {chave: grupos[chave] for chave in chaves_aleatorias}

            # Cria o markup para os botões
            markup = InlineKeyboardMarkup()

            # Se houver grupos fixados, adicione-os primeiro
            if grupos_fixados:
                # Adiciona botões com os grupos fixados
                buttons = [InlineKeyboardButton(text=f"📌 {html.escape(grupo[0])} 📌", url=grupo[1]) for grupo in grupos_fixados.values()]

                # Adiciona o primeiro botão fixado na primeira linha

            # Função para adicionar botões em pares de 2
            def adicionar_botoes_em_pares(grupos):
                botao_par = []  # Lista para armazenar pares de botões
                for chave, valores in grupos:
                    nome, link = valores
                    botao_par.append(InlineKeyboardButton(text=nome, url=link))

                    # Quando atingimos 2 botões, os coloca em uma nova linha
                    if len(botao_par) == 2:
                        markup.add(*botao_par)  # Adiciona os dois botões na linha
                        botao_par = []  # Reseta a lista para o próximo par

                # Caso reste 1 botão na última linha, adiciona ele sozinho
                if botao_par:
                    markup.add(*botao_par)
            if len(buttons) >= 1:
                markup.add(buttons[0])  # 1 botão na primeira linha


            # Adicionar os 10 primeiros
            adicionar_botoes_em_pares(list(grupos_selecionados.items())[:10])  # 10 primeiros

            # Adiciona o segundo botão fixado após os 10 primeiros
            if len(buttons) > 1:
                markup.add(buttons[1])  # Adiciona o segundo botão fixado na segunda linha

            # Adicionar os 10 intermediários
            adicionar_botoes_em_pares(list(grupos_selecionados.items())[10:20])  # 10 intermediários

            # Adicionar os 10 últimos
            if len(buttons) >= 1:
                    markup.add(buttons[2])  # 1 botão na primeira linha
            adicionar_botoes_em_pares(list(grupos_selecionados.items())[20:])   # 10 últimos


            markup.add(
                InlineKeyboardButton('⚙ 𝗔𝗗𝗜𝗖𝗜𝗢𝗡𝗔𝗥 𝗚𝗥𝗨𝗣𝗢 🔗', url="https://t.me/BravusListBot")
            )
            # Envia a mensagem e armazena a resposta
            msg = bot.send_message(grupo_id, mensagem_lista, reply_markup=markup, parse_mode='HTML')
            print(f"✅ Lista enviada para o grupo {grupo_id}.")
            # Salva os detalhes da mensagem enviada no banco de dados
            cursor.execute("""
                INSERT INTO listas_rastreadas (chat_id, mensagem_id, data_envio)
                VALUES (%s, %s, %s)
            """, (grupo_id, msg.message_id, datetime.datetime.now()))
            conn.commit()
            print(f"✅ Registro inserido na tabela ListaRastreada para o grupo {grupo_id}.")
        except Exception as e:
            print(f"❌ Erro ao enviar mensagem para o grupo {grupo_id}: {e}")

            # Fechar a conexão do banco
    cursor.close()
    conn.close()
# # Agendar tarefas
schedule.every().day.at("05:00").do(carregar_dados)
schedule.every().day.at("09:30").do(primeira_lista)
schedule.every().day.at("18:30").do(primeira_lista)


def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)


# Iniciar threads para polling do bot e o agendamento
thread_schedule = threading.Thread(target=run_schedule,  daemon=True)
thread_schedule.start()



# Executar o bot.polling() no main thread
bot.polling()
