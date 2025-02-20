import telebot
from botoes_ADM import botoesMenuAdm,  botoesEditarAdm, botoesEditarFixados, botoesEditarMensagens, botoesExcluirAdm, botoesConfirmarExlusao
import mysql.connector
from mysql.connector import Error
from telebot import types
import re
import datetime

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
        print(f"Erro de conexão: {err}")
        return None


aguardando_adm_id = {}
aguardando_exclusao = {}
aguardando_edicao_msg = {}

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
    except Exception as e:
        print(f"Erro na função 'handleEditarMensagens': {e}")

def handleConfirmarExlusao(bot, call):

    bot.send_message(call.message.chat.id, "Tem certeza que deseja excluir este administrador?", reply_markup=botoesConfirmarExlusao())

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


def handleEditarFixados(bot, call):
    try:
        grupo_id = int(call.data.split('selecionar_')[1])  # Extrai o ID do grupo do callback
        # Solicita o novo ID do grupo
        msg = bot.send_message(call.message.chat.id, f"Por favor, envie o novo ID para o grupo de ID {grupo_id}:")
        # Define o próximo passo
        bot.register_next_step_handler(msg, processar_id_grupo, grupo_id)
    except Exception as e:
        print(f"Erro na função 'handleEditar': {e}")


# Função para salvar a mensagem editada
def salvar_mensagem_editada(message):
    chat_id = message.chat.id
    nova_mensagem = message.text

    if chat_id in aguardando_edicao_msg:
        campo = aguardando_edicao_msg[chat_id]

        # Validação do link de suporte
        if campo == 'Mensagem_aroba_suporte' and not validar_link(nova_mensagem):
            msg = bot.send_message(chat_id, "Link inválido! Certifique-se de começar com http:// ou https://")
            bot.register_next_step_handler(msg, salvar_mensagem_editada)
            return
        

        if campo == 'editar_informacoes' and not validar_link(nova_mensagem):
            msg = bot.send_message(chat_id, "Link inválido! Certifique-se de começar com http:// ou https://")
            bot.register_next_step_handler(msg, salvar_mensagem_editada)
            return
        
        conexao = conectar_ao_banco()

        if not conexao:
            bot.send_message(chat_id, "Erro ao acessar o banco de dados. Tente novamente mais tarde.")
            return

        cursor = conexao.cursor()

        try:
            cursor.execute("SELECT * FROM mensagens LIMIT 1")
            mensagem = cursor.fetchone()

            if not mensagem:
                cursor.execute("INSERT INTO mensagens (Mensagem_aroba_suporte) VALUES ('')")
                conexao.commit()
                cursor.execute("SELECT * FROM mensagens LIMIT 1")
                mensagem = cursor.fetchone()

            # Atualiza o campo da mensagem com o novo texto
            cursor.execute(f"UPDATE mensagens SET {campo} = %s WHERE id = %s", (nova_mensagem, mensagem[0]))
            conexao.commit()

            bot.send_message(chat_id, f"{campo.replace('_', ' ')} atualizado com sucesso!")
        except Exception as e:
            bot.send_message(chat_id, "Erro ao atualizar a mensagem.")
            print(e)
        finally:
            cursor.close()
            conexao.close()
            aguardando_edicao_msg.pop(chat_id, None)

# Função para validar o link
def validar_link(link):
    padrao = re.compile(r"^https?://\S+")
    return bool(padrao.match(link))

# Função para receber o ID do administrador
def receber_id_adm(message):
    chat_id = message.chat.id

    if chat_id not in aguardando_adm_id:
        bot.send_message(chat_id, "Algo deu errado. Comece o processo novamente.")
        return

    cursor = None  # Garantir que a variável cursor seja inicializada
    conexao = None  # Garantir que a variável conexao seja inicializada

    try:
        novo_id = message.text.strip()  # Pega o ID e remove espaços extras

        # Verificar se o ID é numérico
        if not novo_id.isdigit():
            bot.send_message(chat_id, "Por favor, envie um ID válido (somente números).")
            return

        novo_id = str(novo_id)  # Converte o texto para string

        # Conectar ao banco de dados
        conexao = conectar_ao_banco()
        if not conexao:
            bot.send_message(chat_id, "Erro ao acessar o banco de dados.")
            return

        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (novo_id,))
        usuario = cursor.fetchone()

        if usuario:
            nome_adm = usuario[1]  # Nome do usuário encontrado

            # Adicionar na tabela de administradores
            cursor.execute("INSERT INTO admins (id_usuario, nome_adm) VALUES (%s, %s)", (novo_id, nome_adm))
            conexao.commit()

            bot.send_message(chat_id, f"Administrador {nome_adm} (ID: {novo_id}) adicionado com sucesso!")
        else:
            bot.send_message(chat_id, "ID não encontrado na tabela de usuários. Processo encerrado.")

    except Exception as e:
        # Tratar qualquer erro inesperado
        bot.send_message(chat_id, f"Erro ao processar sua solicitação: {str(e)}")
        print(f"Erro: {str(e)}")

    finally:
        # Fechar cursor e conexao se definidos
        if cursor:
            cursor.close()
        if conexao:
            conexao.close()

        # Limpa o estado do chat no dicionário
        aguardando_adm_id.pop(chat_id, None)


# Função para processar o ID do grupo
def processar_id_grupo(message, grupo_id):
    try:
        # Converte o ID enviado pelo usuário para inteiro
        novo_grupo_id = int(message.text.strip())

        conexao = conectar_ao_banco()
        if not conexao:
            bot.send_message(message.chat.id, "Erro ao acessar o banco de dados. Tente novamente mais tarde.")
            return

        cursor = conexao.cursor(dictionary=True)

        # Verifica se o novo ID já está marcado como fixado
        cursor.execute("SELECT * FROM grupos_e_canais WHERE id = %s AND fixado = TRUE", (novo_grupo_id,))
        grupo_existente = cursor.fetchone()

        if grupo_existente:
            bot.send_message(
                message.chat.id,
                f"❌ O grupo '{grupo_existente['nome']}' já está fixado. Não é possível fixá-lo novamente."
            )
            return

        # Busca no banco de dados pelo novo ID fornecido
        cursor.execute("SELECT * FROM grupos_e_canais WHERE id = %s", (novo_grupo_id,))
        grupo = cursor.fetchone()

        if grupo:
            # Atualiza o campo fixado para True no grupo atual
            cursor.execute("SELECT * FROM grupos_e_canais WHERE id = %s", (grupo_id,))
            grupo_atual = cursor.fetchone()

            if grupo_atual:
                cursor.execute("UPDATE grupos_e_canais SET fixado = FALSE WHERE id = %s", (grupo_id,))
                cursor.execute("UPDATE grupos_e_canais SET fixado = TRUE WHERE id = %s", (novo_grupo_id,))
                conexao.commit()

                # Envia uma confirmação para o usuário
                resposta = (
                    f"✅ Grupo fixado atualizado com sucesso!\n"
                    f"**Nome:** {grupo['nome']}\n"
                    f"**Link:** {grupo['link'] or 'Nenhum link disponível'}\n"
                    f"**Tipo:** {grupo['tipo']}\n"
                    f"**Aprovação:** {'Sim' if grupo['apro'] else 'Não'}\n"
                    f"**Exclusões:** {grupo['exclusoes']}"
                )
            else:
                resposta = f"❌ Nenhum grupo encontrado com o ID: {grupo_id}."

        # Envia a resposta para o usuário
        bot.send_message(message.chat.id, resposta, parse_mode="Markdown")

        cursor.close()
        conexao.close()

    except ValueError:
        # Caso o usuário envie algo que não seja um número
        bot.send_message(message.chat.id, "❌ O ID enviado não é válido. Por favor, envie um número inteiro.")
    except Exception as e:
        # Tratamento genérico de erro
        bot.send_message(message.chat.id, f"❌ Ocorreu um erro: {str(e)}")

