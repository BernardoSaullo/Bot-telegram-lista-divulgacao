from botoes_ADM import botoesConfirmarExlusao
from mysql.connector import Error
from telebot import types
import datetime
from config import conectar_ao_banco
from funcao_auxiliares import *


def handleDisparoEmMassa(bot, message):
    conexao = conectar_ao_banco()
    if not conexao:
        bot.send_message(message.chat.id, "Erro ao acessar o banco de dados. Tente novamente mais tarde.")
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        # Verificar se o usuário é um administrador
        cursor.execute("SELECT id_usuario FROM admins")
        ids = [admin["id_usuario"] for admin in cursor.fetchall()]

        if str(message.from_user.id) not in ids:
            bot.send_message(message.chat.id, "Acesso negado.")
            return

        cursor.execute("SELECT mensagem_em_massa FROM mensagens")
        mensagem = cursor.fetchone()

        cursor.execute("SELECT id FROM usuarios")
        ids = [usuario["id"] for usuario in cursor.fetchall()]

        for id in ids:
            try:
                bot.send_message(id, mensagem["mensagem_em_massa"])
            except Exception as e:
                print(f"Erro ao enviar mensagem para o usuário {id}: {e}")
            

    except Error as e:
        print(f"Erro ao consultar os admins no banco de dados: {e}")
        bot.send_message(message.chat.id, "Erro ao processar sua solicitação.")

    finally:
        cursor.close()
        conexao.close()

def handleBanirUsuario(bot, message):
    conexao = conectar_ao_banco()
    if not conexao:
        bot.send_message(message.chat.id, "Erro ao acessar o banco de dados. Tente novamente mais tarde.")
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        # Verificar se o usuário é um administrador
        cursor.execute("SELECT id_usuario FROM admins")
        ids = [admin["id_usuario"] for admin in cursor.fetchall()]

        if str(message.from_user.id) not in ids:
            bot.send_message(message.chat.id, "Acesso negado.")
            return

        # Solicitar o ID do usuário a ser banido
        msg = bot.send_message(message.chat.id, "Por favor, envie o ID do usuário que deseja banir:")

        

        bot.register_next_step_handler(msg, processarBanimentoUsuario)

    except Error as e:
        print(f"Erro ao consultar os admins no banco de dados: {e}")
        bot.send_message(message.chat.id, "Erro ao processar sua solicitação.")

    finally:
        cursor.close()
        conexao.close()

def handleBanirGrupos(bot, message):
    conexao = conectar_ao_banco()
    if not conexao:
        bot.send_message(message.chat.id, "Erro ao acessar o banco de dados. Tente novamente mais tarde.")
        return

    cursor = conexao.cursor(dictionary=True)

    try:
        # Verificar se o usuário é um administrador
        cursor.execute("SELECT id_usuario FROM admins")
        ids = [admin["id_usuario"] for admin in cursor.fetchall()]

        if str(message.from_user.id) not in ids:
            bot.send_message(message.chat.id, "Acesso negado.")
            return

        # Solicitar o ID do usuário a ser banido
        msg = bot.send_message(message.chat.id, "Por favor, envie o ID do Grupo que deseja banir:")

        bot.register_next_step_handler(msg, processarBanimentoGrupos)

    except Error as e:
        print(f"Erro ao consultar os admins no banco de dados: {e}")
        bot.send_message(message.chat.id, "Erro ao processar sua solicitação.")

    finally:
        cursor.close()
        conexao.close()



def handleListarGrupos(bot, message):
    conexao = conectar_ao_banco()
    if not conexao:
        bot.send_message(message.chat.id, "Erro ao acessar o banco de dados. Tente novamente mais tarde.")
        return

    cursor = conexao.cursor(dictionary=True)
    try:
        # Verificar se o usuário é um administrador
        cursor.execute("SELECT id_usuario FROM admins")
        ids = [admin["id_usuario"] for admin in cursor.fetchall()]
        print(ids)

        if str(message.from_user.id) not in ids:
            bot.send_message(message.chat.id, "Acesso negado.")
            return

        # Buscar os grupos que não estão aprovados
        cursor.execute("SELECT id, nome, link FROM grupos_e_canais WHERE apro IS NOT TRUE")
        grupos = cursor.fetchall()

        if not grupos:
            bot.send_message(message.chat.id, "Nenhum grupo encontrado.")
            return

        # Enviar informações de cada grupo
        for grupo in grupos:
            # Criar botões "Aprovar", "Banir Grupo" e "Banir Usuário"
            markup = types.InlineKeyboardMarkup()
            approve_button = types.InlineKeyboardButton("Aprovar Grupo", callback_data=f"aprovar_{grupo['id']}")
            ban_group_button = types.InlineKeyboardButton("Banir Grupo", callback_data=f"banir_grupo_{grupo['id']}")
            ban_user_button = types.InlineKeyboardButton("Banir Usuário", callback_data=f"banir_usuario_{grupo['id']}")
            markup.add(approve_button, ban_group_button, ban_user_button)

            # Enviar a mensagem com o link e os botões
            bot.send_message(
                message.chat.id,
                f"Grupo: {grupo['nome']}\nLink: {grupo['link']}",
                reply_markup=markup
            )

    except Error as e:
        print(f"Erro ao consultar grupos no banco de dados: {e}")
        bot.send_message(message.chat.id, "Erro ao processar sua solicitação.")
    finally:
        cursor.close()
        conexao.close()


def handle_aprova_ou_rejeita(bot, call):
    try:
        action, identifier = call.data.split('_', 1)
        conexao = conectar_ao_banco()
    
        if not conexao:
            bot.send_message(call.message.chat.id, "Erro ao acessar o banco de dados. Tente novamente mais tarde.")
            return
    
        cursor = conexao.cursor(dictionary=True)

        if action == 'aprovar':
            # Aprovar o grupo
            group_id = int(identifier)
            cursor.execute("SELECT * FROM grupos_e_canais WHERE id = %s", (group_id,))
            grupo = cursor.fetchone()

            if not grupo:
                bot.answer_callback_query(call.id, "Grupo não encontrado!")
                return

            # Aprovar o grupo
            cursor.execute("UPDATE grupos_e_canais SET apro = TRUE WHERE id = %s", (group_id,))
            conexao.commit()

            bot.answer_callback_query(call.id, "Grupo aprovado com sucesso!")

            bot.send_message(grupo['id_usuario'], f"Seu grupo {grupo['nome']} foi aprovado! Agora o bot enviará a lista todos os dias.")

        elif action == 'banir':
            sub_action, group_id = identifier.split('_', 1)
            group_id = int(group_id)

            if sub_action == 'grupo':
                # Banir o grupo
                cursor.execute("SELECT * FROM grupos_e_canais WHERE id = %s", (group_id,))
                grupo = cursor.fetchone()

                if not grupo:
                    bot.answer_callback_query(call.id, "Grupo não encontrado!")
                    return
                bot.leave_chat(group_id)
                # Adicionar o grupo à tabela de banidos antes de excluir
                cursor.execute("INSERT INTO grupos_e_canais_banidos (id, tipo, data_banimento) VALUES (%s, %s, %s)",
                               (grupo['id'], grupo['tipo'], datetime.datetime.now()))
                conexao.commit()

                # Excluir o grupo da tabela original
                cursor.execute("DELETE FROM grupos_e_canais WHERE id = %s", (group_id,))
                conexao.commit()

                bot.answer_callback_query(call.id, "Grupo banido com sucesso!")

            elif sub_action == 'usuario':
                # Banir o usuário associado ao grupo
                cursor.execute("SELECT * FROM grupos_e_canais WHERE id = %s", (group_id,))
                grupo = cursor.fetchone()

                if not grupo:
                    bot.answer_callback_query(call.id, "Grupo não encontrado!")
                    return

                # Buscar o usuário associado ao grupo
                cursor.execute("SELECT * FROM usuarios WHERE id = %s", (grupo['id_usuario'],))
                usuario = cursor.fetchone()

                if not usuario:
                    bot.answer_callback_query(call.id, "Usuário não encontrado!")
                    return

                # Deletar todos os grupos do usuário
                cursor.execute("DELETE FROM grupos_e_canais WHERE id_usuario = %s", (usuario['id'],))
                conexao.commit()

                # Mover o usuário para a tabela de banidos
                cursor.execute("INSERT INTO usuarios_banidos (id) VALUES (%s)", (usuario['id'],))
                conexao.commit()

                # Remover o usuário da tabela de usuários
                cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario['id'],))
                conexao.commit()

                bot.answer_callback_query(call.id, f"Usuário {usuario['nome_usuario']} banido com sucesso!")

    except Error as e:
        print(f"Erro na função 'handleAprovar_banir': {e}")
        bot.send_message(call.message.chat.id, "Erro ao processar sua solicitação.")
    finally:
        cursor.close()
        conexao.close()

    # Remover os botões após a ação
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)


def handleConfirmarExlusao(bot, call):

    bot.send_message(call.message.chat.id, "Tem certeza que deseja excluir este administrador?", reply_markup=botoesConfirmarExlusao())