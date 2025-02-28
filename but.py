import threading
import schedule
import time
import mysql.connector

from ADM_handlers_edicao import handleMenuAdm, handleEditar, handleEditarAdm, handleEditarFixados, handleEditarMensagens, handleInserirFixado

from ADM_handlers_gereciamento import handleDisparoEmMassa, handleBanirUsuario, handleBanirGrupos, handleListarGrupos, handle_aprova_ou_rejeita

from handlers_User import handleMenu, handleCallMenu

from telebot.types import ChatMemberUpdated
import logging
from config import conectar_ao_banco, bot
from funcoes_lista_divulgacao import carregar_dados, primeira_lista



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

@bot.message_handler(commands=['banir_usuario'])
def banir_usuario(message):
    handleBanirUsuario(bot, message)

@bot.message_handler(commands=['banir_grupo'])
def banir_grupo(message):
    handleBanirGrupos(bot, message)

@bot.message_handler(commands=['disparo_em_massa'])
def disparo_em_massa(message):
    handleDisparoEmMassa(bot, message)

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

@bot.callback_query_handler(func=lambda call: call.data.startswith('inserir_'))
def callback_inserir_fixado(call):
    handleInserirFixado(bot, call)


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
        print(chat_id)
        try:
            # Conectar ao banco de dados
            connection = conectar_ao_banco()
            if connection is None:
                bot.leave_chat(chat_id)
                print('sem conexão como banco de dados')
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

            if members_count < 0:
                bot.leave_chat(chat_id)
                bot.send_message(user_id, 'Você não tem integrantes suficientes para participar da lista🙁')
                cursor.close()
                connection.close()
                return

            # Tentar pegar o link do grupo
            try:
                link = bot.export_chat_invite_link(chat_id)
            except Exception as e:
                bot.send_message(user_id, '❌ Você não concedeu as permissões corretas para o bot ( Gerenciar mensagens, Adicionar membros, Apagar mensagens e Fixar )')
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
            try:
                bot.send_message(chat_id, "✅🥳| Parabéns, você acaba de entrar a melhor lista de grupos do Telegram!")
            except Exception as e:
                bot.send_message(user_id, '❌ Você não concedeu as permissões corretas para o bot ( Gerenciar mensagens, Adicionar membros, Apagar mensagens e Fixar )')
                print(f"Erro ao mandar msg: {e}")
                bot.leave_chat(chat_id)
                cursor.close()
                connection.close()
                return
                
            cursor.execute("SELECT id FROM grupos_e_canais WHERE id = %s", (chat_id,))
            existing_group = cursor.fetchone()

            if existing_group:
                print("Grupo/Canal já existe no banco. Nenhuma ação necessária.")
              
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
# # Agendar tarefas
schedule.every().day.at("23:20").do(carregar_dados)
# schedule.every().day.at("00:00").do(primeira_lista)
schedule.every().day.at("05:20").do(carregar_dados)

# schedule.every().day.at("06:00").do(primeira_lista)
schedule.every().day.at("11:20").do(carregar_dados)

# schedule.every().day.at("12:00").do(primeira_lista)
schedule.every().day.at("17:20").do(carregar_dados)

# schedule.every().day.at("18:00").do(primeira_lista)

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# carregar_dados()
# primeira_lista()
# Iniciar threads para polling do bot e o agendamento
thread_schedule = threading.Thread(target=run_schedule,  daemon=True)
thread_schedule.start()


# Executar o bot.polling() no main thread
while True:
    try:
        bot.polling(non_stop=True, timeout=10, long_polling_timeout=20)
    except Exception as e:
        print(f"Erro encontrado: {e}")

