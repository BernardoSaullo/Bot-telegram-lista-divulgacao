import mysql.connector
from mysql.connector import Error
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from botoes_User import botoesMenuUser, botaoMeuPerfil, botoesAdicaoCanalouGrupo, botaoRegras
from telebot import types
import re
import datetime

def conectar_ao_banco():
    try:
        return mysql.connector.connect(
                host="127.0.0.1",
                user="root",
                password="root",
                database="ItsInvictus"
            )
    except mysql.connector.Error as err:
        return None

# Token do bot
bot = telebot.TeleBot(token="7729962379:AAFWDwssjjJ2RldSg5TlJGwoHosWcvwWiGQ", parse_mode='HTML')

# Dicionário global para armazenar o message_id por chat_id ou user_id
boas_vindas_message_ids = {}

# Função para conexão com o banco de dados
def handleMenu(bot, message):
    conexao = conectar_ao_banco()
    if not conexao:
        bot.send_message(message.chat.id, "Erro ao acessar o banco de dados. Tente novamente mais tarde.")
        return

    cursor = conexao.cursor(dictionary=True)
    try:
        # Consultar IDs banidos
        cursor.execute("SELECT id FROM usuarios_banidos")
        ids_banidos = [banido["id"] for banido in cursor.fetchall()]

        id_usuario = message.from_user.id

        if id_usuario not in ids_banidos:
            nome_usuario = message.from_user.first_name if message.from_user.first_name else "Não informado"

            # Verificar se o usuário já existe
            cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id_usuario,))
            existing_user = cursor.fetchone()

            if existing_user is None:
                entrada = datetime.datetime.now()

                # Inserir novo usuário
                cursor.execute(
                    "INSERT INTO usuarios (id, nome_usuario, data_registro) VALUES (%s, %s, %s)",
                    (id_usuario, nome_usuario, entrada)
                )
                conexao.commit()

                boas_vindas = f'Bem-vindo <a href="https://t.me/Teste1_984o64_bot">{nome_usuario}</a>!'
                mensagem_boas_vindas = bot.send_message(message.chat.id, boas_vindas, reply_markup=botoesMenuUser())

                # Armazena o message_id no dicionário global
                boas_vindas_message_ids[message.chat.id] = mensagem_boas_vindas.message_id
            else:
                boas_vindas = f'Bem-vindo de volta <a href="https://t.me/Teste1_984o64_bot"><b>{nome_usuario}</b></a>!'

            # Obter mensagem de início
            cursor.execute("SELECT mensagem_inicio FROM mensagens LIMIT 1")
            mensagem = cursor.fetchone()
            mensagem_texto = mensagem["mensagem_inicio"] if mensagem else "Mensagem padrão de início."

            bot.send_message(message.chat.id, boas_vindas + '\n\n' + mensagem_texto, reply_markup=botoesMenuUser())
        else:
            bot.send_message(message.chat.id, '🚫 Você está PROIBIDO de acessar este bot 🚫')

    except Error as e:
        print(f"Erro ao executar consulta MySQL: {e}")
        bot.send_message(message.chat.id, "Ocorreu um erro ao processar sua solicitação. Tente novamente mais tarde.")
    finally:
        cursor.close()
        conexao.close()


def handleCallMenu(bot, call):
    if call.data == 'menu_meu_perfil':
        # Aqui você usa o message_id armazenado no dicionário global
        if call.message.chat.id in boas_vindas_message_ids:
            message_id = boas_vindas_message_ids[call.message.chat.id]
            bot.delete_message(chat_id=call.message.chat.id, message_id=message_id)

        conexao = conectar_ao_banco()
        if not conexao:
            bot.answer_callback_query(call.id, "Erro ao acessar o banco de dados. Tente novamente mais tarde.")
            return

        cursor = conexao.cursor(dictionary=True)
        user_id = call.from_user.id

        try:

            # Buscar usuário no banco de dados
            cursor.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,))
            usuario = cursor.fetchone()

            if not usuario:
                bot.answer_callback_query(call.id, "Usuário não encontrado!")
                return

            # Buscar quantidade de grupos e canais do usuário
            cursor.execute("SELECT COUNT(*) AS total FROM grupos_e_canais WHERE id_usuario = %s AND tipo = 'Grupo'", (user_id,))
            total_grupos = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM grupos_e_canais WHERE id_usuario = %s AND tipo = 'Canal'", (user_id,))
            total_canais = cursor.fetchone()["total"]

            # Mensagem de perfil
            mensagem = f"""⚙️ 𝗚𝗲𝗿𝗲𝗻𝗰𝗶𝗲 e veja as informações do seu perfil aqui, como canais/grupos cadastrados e muito mais!

<blockquote>🧑🏻‍💻 • 𝗠𝗲𝘂 𝗽𝗲𝗿𝗳𝗶𝗹
┣ 📢 <b>Canais</b> : {total_canais}
┗ 💬 <b>Grupos</b> : {total_grupos}

📆 <b>Registro</b>: {usuario['data_registro'].strftime('%d/%m/%Y')}

🔗 Seus Canais/Grupos</blockquote>"""

            # Buscar grupos e canais do usuário
            cursor.execute("SELECT nome, link, apro FROM grupos_e_canais WHERE id_usuario = %s", (user_id,))
            grupos_canais = cursor.fetchall()

            for grupo in grupos_canais:
                if grupo["apro"]:
                    mensagem += f"- <b>{grupo['nome']}</b>: <a href=\"{grupo['link']}\">Acessar</a>\n"  # Aprovados
                else:
                    mensagem += f"- <b>{grupo['nome']}</b>: <a href=\"{grupo['link']}\">Acessar</a> (Aguardando Aprovação)\n"

            # Criação do markup
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🏠 Início", callback_data='menu_inicio'))

            # Enviar a mensagem
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=mensagem, reply_markup=markup)


        except Error as e:
            print(f"Erro ao executar consulta MySQL: {e}")
            bot.answer_callback_query(call.id, "Erro ao processar a solicitação.")
        finally:
            cursor.close()
            conexao.close()

    elif call.data == 'menu_regras':
        conexao = conectar_ao_banco()
        if not conexao:
            bot.answer_callback_query(call.id, "Erro ao acessar o banco de dados. Tente novamente mais tarde.")
            return

        cursor = conexao.cursor(dictionary=True)
        try:
            # Obter mensagem de regras
            cursor.execute("SELECT mensagem_regras FROM mensagens LIMIT 1")
            mensagem = cursor.fetchone()["mensagem_regras"]

            # bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)

            markup = botaoRegras()

            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=mensagem, reply_markup=markup, parse_mode='HTML')

        except Error as e:
            print(f"Erro ao executar consulta MySQL: {e}")
            bot.answer_callback_query(call.id, "Erro ao processar a solicitação.")
        finally:
            cursor.close()
            conexao.close()

    elif call.data == 'menu_add':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Adicione seu Grupo/Canal:", reply_markup=botoesAdicaoCanalouGrupo())

    elif call.data == 'menu_inicio':

        conexao = conectar_ao_banco()
        if not conexao:
            bot.answer_callback_query(call.id, "Erro ao acessar o banco de dados. Tente novamente mais tarde.")
            return

        cursor = conexao.cursor(dictionary=True)

        markup = botoesMenuUser()
        cursor.execute("SELECT mensagem_inicio FROM mensagens LIMIT 1")
        mensagem = cursor.fetchone()

        mensagem_texto = mensagem["mensagem_inicio"] if mensagem else "Mensagem padrão de início.																	"

        if call.message.text != mensagem_texto or call.message.reply_markup != markup:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=mensagem_texto, reply_markup=markup)
        else:
            print("A mensagem e o teclado são os mesmos. Nenhuma alteração necessária.")

        cursor.close()
        conexao.close()
