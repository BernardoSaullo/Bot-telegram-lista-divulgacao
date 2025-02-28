from botoes_ADM import botoesMenuAdm,  botoesEditarAdm, botoesEditarFixados, botoesEditarMensagens, botoesExcluirAdm, botoesConfirmarExlusao
from mysql.connector import Error
from telebot import types
from config import conectar_ao_banco, aguardando_adm_id, aguardando_exclusao, aguardando_edicao_msg
from funcao_auxiliares import *


def handleMenuAdm(bot, message):
    # Conecta ao banco de dados
    conexao = conectar_ao_banco()
    if not conexao:
        bot.send_message(message.chat.id, "Erro ao acessar o banco de dados. Tente novamente mais tarde.")
        return

    cursor = conexao.cursor(dictionary=True)
    try:
        # Obter todos os IDs de admins
        cursor.execute("SELECT id_usuario FROM admins")
        ids = [str(admin["id_usuario"]) for admin in cursor.fetchall()]  # Converte para string para comparação

        if str(message.from_user.id) in ids:
            # Usuário autorizado
            bot.send_message(message.chat.id, "Escolha uma opção:", reply_markup=botoesMenuAdm())
        else:
            # Acesso negado
            print('Acesso negado para o usuário:', message.from_user.id)

    except Error as e:
        print(f"Erro ao consultar os admins no banco de dados: {e}")
        bot.send_message(message.chat.id, "Ocorreu um erro ao processar sua solicitação. Tente novamente mais tarde.")
    finally:
        cursor.close()
        conexao.close()

def handleEditar(bot, call):

    if call.data == 'editar_adms':
        bot.send_message(call.message.chat.id, "Escolha uma opção:", reply_markup=botoesEditarAdm())

    elif call.data == 'editar_mensagens':
        bot.send_message(call.message.chat.id, 'Qual mensagem você gostaria de Editar?', reply_markup=botoesEditarMensagens())

    elif call.data == 'editar_fixados':
        bot.send_message(call.message.chat.id, "Selecione um grupo para editar:", reply_markup=botoesEditarFixados())

    elif call.data == 'editar_suporte':
        msg = bot.send_message(call.message.chat.id, "Envie o novo link de suporte (comece com http ou https):")
        aguardando_edicao_msg[call.message.chat.id] = 'Mensagem_aroba_suporte'
        bot.register_next_step_handler(msg, salvar_mensagem_editada)
    elif call.data == 'editar_informacoes':
        msg = bot.send_message(call.message.chat.id, "Envie o novo link de suporte (comece com http ou https):")
        aguardando_edicao_msg[call.message.chat.id] = 'Mensagem_aroba_informacoes'
        bot.register_next_step_handler(msg, salvar_mensagem_editada)


def handleEditarAdm(bot, call):
    try:

        if call.data == 'adm_adicionar':
            msg = bot.send_message(call.message.chat.id, "Envie o ID do novo administrador:")
            aguardando_adm_id[call.message.chat.id] = {'step': 'id'}
            print(aguardando_adm_id)
            bot.register_next_step_handler(msg, receber_id_adm)
    
    
        elif call.data == 'adm_excluir':
            bot.send_message(call.message.chat.id, "Escolha o administrador que deseja excluir:", reply_markup=botoesExcluirAdm())
    
        elif call.data.startswith('adm_excluir_'):
    
            adm_id = call.data.split('_')[2]
            aguardando_exclusao[call.message.chat.id] = adm_id
            bot.send_message(call.message.chat.id, "Tem certeza que deseja excluir este administrador?", reply_markup=botoesConfirmarExlusao())
    
        elif call.data == 'adm_confirmar_exclusao':
    
            adm_id = aguardando_exclusao.pop(call.message.chat.id, None)
            if adm_id:
                conexao = conectar_ao_banco()
                if not conexao:
                    bot.send_message(call.message.chat.id, "Erro ao acessar o banco de dados. Tente novamente mais tarde.")
                    return
    
                cursor = conexao.cursor()
                try:
                    # Excluir o administrador com o ID especificado
                    cursor.execute("DELETE FROM admins WHERE id_usuario = %s", (adm_id,))
                    conexao.commit()
    
                    bot.send_message(call.message.chat.id, "Administrador excluído com sucesso!")
                except Error as e:
                    print(f"Erro ao excluir administrador no banco de dados: {e}")
                    bot.send_message(call.message.chat.id, "Erro ao processar a exclusão do administrador.")
                finally:
                    cursor.close()
                    conexao.close()
    
    
        elif call.data == 'adm_cancelar_exclusao':
            aguardando_exclusao.pop(call.message.chat.id, None)
            bot.send_message(call.message.chat.id, "Exclusão cancelada.")
    except Exception as e:
        print(f"Erro na função 'handleEditar': {e}")


def handleEditarMensagens(bot, call):
    try:

        chat_id = call.message.chat.id
    
        if call.data == 'editar_msg_incio':
            print('entrou')
            msg = bot.send_message(chat_id, "Envie a nova mensagem de início:")
            aguardando_edicao_msg[chat_id] = 'Mensagem_Inicio'
            bot.register_next_step_handler(msg, salvar_mensagem_editada)
  
        elif call.data == 'editar_msg_regras':
            msg = bot.send_message(chat_id, "Envie a nova mensagem de regras:")
            aguardando_edicao_msg[chat_id] = 'Mensagem_Regras'
            bot.register_next_step_handler(msg, salvar_mensagem_editada)
  
        elif call.data == 'editar_msg_lista':
            msg = bot.send_message(chat_id, "Envie a nova mensagem da lista:")
            aguardando_edicao_msg[chat_id] = 'Mensagem_Lista'
            bot.register_next_step_handler(msg, salvar_mensagem_editada)

        elif call.data == 'editar_msg_disparo':
            msg = bot.send_message(chat_id, "Envie a nova mensagem de disparo em massa:")
            aguardando_edicao_msg[chat_id] = 'mensagem_em_massa'

            bot.register_next_step_handler(msg, salvar_mensagem_editada)

    except Exception as e:
        print(f"Erro na função 'handleEditarMensagens': {e}")



def handleEditarFixados(bot, call):
    try:
        grupo_id = int(call.data.split('selecionar_')[1])  # Extrai o ID do grupo do callback

        # Solicita o novo ID do grupo
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Link", callback_data=f"inserir_link_{grupo_id}"))
        markup.add(types.InlineKeyboardButton("Grupo", callback_data=f"inserir_grupo_{grupo_id}"))

        bot.send_message(call.message.chat.id, "Escolha pelo que deseja inserir:", reply_markup=markup)
    except Exception as e:
        print(f"Erro na função 'handleEditarFixados': {e}")

def handleInserirFixado(bot, call):
    try:
        action, fixado_id = call.data.split('_')[1], int(call.data.split('_')[2])

        if action == 'link':

            msg = bot.send_message(call.message.chat.id, "Por favor, envie o Texto de Exibição e o Link para o botão fixado")
            bot.register_next_step_handler(msg, processar_link, fixado_id)
        elif action == 'grupo':

            msg = bot.send_message(call.message.chat.id, "Por favor, envie o ID do grupo ou canal para o botão fixado")
            bot.register_next_step_handler(msg, processar_id_grupo, fixado_id)
    except Exception as e:
        print(f"Erro na função 'handleInserirFixado': {e}")
