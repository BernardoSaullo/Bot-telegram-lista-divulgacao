
from mysql.connector import Error
import re
from config import conectar_ao_banco, bot
from config import conectar_ao_banco, bot, aguardando_adm_id, aguardando_exclusao, aguardando_edicao_msg
import telebot

def processarBanimentoUsuario(message):
    conexao = conectar_ao_banco()
    if not conexao:
        bot.send_message(message.chat.id, "Erro ao acessar o banco de dados. Tente novamente mais tarde.")
        return
    
    cursor = conexao.cursor(dictionary=True)

    try:
        user_id = message.text

        # Verificar se o ID é um número
        if not user_id.isdigit():
            bot.send_message(message.chat.id, "ID inválido. Por favor, envie um número.")
            return

        # Verificar se o ID existe na tabela de usuários
        cursor.execute("SELECT id FROM usuarios WHERE id = %s", (user_id,))
        usuario = cursor.fetchone()

        if not usuario:
            bot.send_message(message.chat.id, "Usuário não encontrado.")
            return

        # Banir o usuário
        cursor.execute("DELETE FROM usuarios WHERE id = %s", (user_id,))
        conexao.commit()

        # Adicionar o ID do usuário na tabela usuarios_banidos
        cursor.execute("INSERT INTO usuarios_banidos (id) VALUES (%s)", (user_id,))
        conexao.commit()

        bot.send_message(message.chat.id, "Usuário banido com sucesso.")

    except Error as e:
        print(f"Erro ao banir o usuário no banco de dados: {e}")
        bot.send_message(message.chat.id, "Erro ao processar sua solicitação.")

    finally:
        cursor.close()
        conexao.close()


def processarBanimentoGrupos(message):
    conexao = conectar_ao_banco()
    if not conexao:
        bot.send_message(message.chat.id, "Erro ao acessar o banco de dados. Tente novamente mais tarde.")
        return
    
    cursor = conexao.cursor(dictionary=True)

    try:
        grupo_id = message.text

        # Verificar se o ID é um número
        # if not grupo_id.isdigit():
        #     bot.send_message(message.chat.id, "ID inválido. Por favor, envie um número.")
        #     return

        # Verificar se o ID existe na tabela de grupos e canais
        cursor.execute("SELECT id, tipo FROM grupos_e_canais WHERE id = %s", (grupo_id,))
        grupo = cursor.fetchone()

        if not grupo:
            bot.send_message(message.chat.id, "Grupo não encontrado.")
            return

        # Banir o grupo
        cursor.execute("DELETE FROM grupos_e_canais WHERE id = %s", (grupo_id,))
        conexao.commit()
        try:
            bot.leave_chat(grupo_id)
            print(f"✅ Bot saiu do grupo {grupo_id} com sucesso.")
        except telebot.apihelper.ApiException as e:
            print(f"❌ Erro ao tentar sair do grupo {grupo_id}: {e}")

        # Adicionar o ID e o tipo do grupo na tabela grupos_e_canais_banidos
        cursor.execute("INSERT INTO grupos_e_canais_banidos (id, tipo) VALUES (%s, %s)", (grupo_id, grupo['tipo']))
        conexao.commit()

        bot.send_message(message.chat.id, "Grupo banido com sucesso.")

    except Error as e:
        print(f"Erro ao banir o grupo no banco de dados: {e}")
        bot.send_message(message.chat.id, "Erro ao processar sua solicitação.")

    finally:
        cursor.close()
        conexao.close()


# Função para salvar a mensagem editada
def salvar_mensagem_editada(message):
    print('entrou salvar_mensagem_editada')
    chat_id = message.chat.id
    nova_mensagem = message.text

    if chat_id in aguardando_edicao_msg:
        print('campo encontrado')
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


        print(campo)

        conexao = conectar_ao_banco()

        if not conexao:
            bot.send_message(chat_id, "Erro ao acessar o banco de dados. Tente novamente mais tarde.")
            return

        cursor = conexao.cursor()

        try:
            cursor.execute("SELECT * FROM mensagens LIMIT 1")
            mensagem = cursor.fetchone()

            # Atualiza o campo da mensagem com o novo texto
            cursor.execute(f"UPDATE mensagens SET {campo} = %s WHERE id = %s", (nova_mensagem, mensagem[0]))
            conexao.commit()
            print('Mensagem atualizada com sucesso')
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

def processar_link(message, fixado_id):
    try:
        texto_exibicao = message.text.split(',')[0].strip()
        link = message.text.split(',')[1].strip()

        if not validar_link(link):
            msg = bot.send_message(message.chat.id, "Link inválido! Certifique-se de começar com http:// ou https://")
            bot.register_next_step_handler(msg, salvar_mensagem_editada)
            return
        
        conexao = conectar_ao_banco()
        if not conexao:
            bot.send_message(message.chat.id, "Erro ao acessar o banco de dados. Tente novamente mais tarde.")
            return
        cursor = conexao.cursor(dictionary=True)

        cursor.execute("UPDATE fixados SET Nome = %s, link = %s WHERE id = %s", (texto_exibicao, link, fixado_id))
        conexao.commit()

        bot.send_message(message.chat.id, "✅ Novo botão fixado atualizado com sucesso!")

    except Exception as e:
        bot.send_message(message.chat.id, f"Erro ao processar sua solicitação: {str(e)}")
        print(f"Erro: {str(e)}")
    finally:
        # Fechar cursor e conexao se definidos
        if cursor:
            cursor.close()
        if conexao:
            conexao.close()
    
    
    

# Função para processar o ID do grupo
def processar_id_grupo(message, fixado_id):
    try:

        # Converte o ID enviado pelo usuário para inteiro
        novo_grupo_id = int(message.text.strip())

        conexao = conectar_ao_banco()
        if not conexao:
            bot.send_message(message.chat.id, "Erro ao acessar o banco de dados. Tente novamente mais tarde.")
            return

        cursor = conexao.cursor(dictionary=True)

        # Busca no banco de dados pelo novo ID fornecido
        cursor.execute("SELECT * FROM grupos_e_canais WHERE id = %s", (novo_grupo_id,))
        grupo = cursor.fetchone()

        if grupo:
            print(grupo['nome'])
            print(fixado_id)
            cursor.execute("UPDATE fixados SET Nome = %s, link = %s WHERE id = %s", (grupo['nome'], grupo['link'], fixado_id))
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
            resposta = f"❌ Nenhum grupo encontrado com o ID: {fixado_id}."

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





import telebot
from telebot import apihelper
from config import bot, conectar_ao_banco

def verificar_grupo_existe(grupo_id):
    try:
        bot.get_chat(grupo_id)
        return True
    except apihelper.ApiException as e:
        if e.error_code == 400 and "chat not found" in e.result:
            return False
        else:
            print(f"Erro ao verificar o grupo: {e}")
            return False

def verificar_todos_os_grupos():
    conexao = conectar_ao_banco()
    if not conexao:
        print("Erro ao acessar o banco de dados. Tente novamente mais tarde.")
        return

    cursor = conexao.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM grupos_e_canais")
        grupos = cursor.fetchall()

        for grupo in grupos:
            grupo_id = grupo['id']
            if verificar_grupo_existe(grupo_id):
                print(f"O grupo com ID {grupo_id} existe.")
            else:
                print(f"O grupo com ID {grupo_id} não existe ou o bot não tem acesso.")
    except Error as e:
        print(f"Erro ao consultar os grupos no banco de dados: {e}")
    finally:
        cursor.close()
        conexao.close()

# Exemplo de uso
