from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import mysql.connector
from mysql.connector import Error

def conectar_ao_banco():
    try:
        conn = mysql.connector.connect(
            host="ItsInvictus.mysql.pythonanywhere-services.com",
            user="ItsInvictus",
            password="root@123",  # Substitua pela sua senha
            database="ItsInvictus$default"
        )
        return conn
    except mysql.connector.Error as err:
        return None


def botoesMenuAdm():
    markup = InlineKeyboardMarkup()

    markup.add(InlineKeyboardButton('👑Editar ADMs', callback_data='editar_adms'))
    markup.add(InlineKeyboardButton('📌Editar Canais e Grupos Fixados', callback_data='editar_fixados'))
    markup.add(InlineKeyboardButton('💬Editar Mensagens', callback_data='editar_mensagens'))
    markup.add(InlineKeyboardButton('🏷️Editar Suporte', callback_data='editar_suporte'))
    markup.add(InlineKeyboardButton('ℹ Editar Informações', callback_data='editar_informacoes'))


    return markup


def botoesEditarAdm():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Adicionar", callback_data='adm_adicionar')
    )
    markup.add(
        InlineKeyboardButton("Excluir", callback_data='adm_excluir')
    )

    return markup



def botoesEditarFixados():
    # Consulta os grupos fixados no banco de dados
    conexao = conectar_ao_banco()
    if not conexao:
        print("Erro ao conectar ao banco para obter grupos fixados.")
        return None

    cursor = conexao.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, nome FROM grupos_e_canais WHERE fixado = TRUE")
        grupos_fixados = cursor.fetchall()

        if not grupos_fixados:
            return None

        # Cria uma inline keyboard com os botões dos grupos fixados
        markup = InlineKeyboardMarkup()
        for grupo in grupos_fixados:
            button = InlineKeyboardButton(text=grupo["nome"], callback_data=f"selecionar_{grupo['id']}")
            markup.add(button)

        return markup
    except Error as e:
        print(f"Erro ao executar consulta MySQL: {e}")
        return None
    finally:
        cursor.close()
        conexao.close()

def botoesEditarMensagens():
    markup = InlineKeyboardMarkup()

    markup.add(InlineKeyboardButton('Editar Mensagem de Incio', callback_data='editar_msg_incio'))
    markup.add(InlineKeyboardButton('Editar Mensagem de Regras', callback_data='editar_msg_regras'))
    markup.add(InlineKeyboardButton('Editar Mensagem Lista', callback_data='editar_msg_lista'))

    return markup

def botoesExcluirAdm():
    # Consulta os admins no banco de dados
    conexao = conectar_ao_banco()
    if not conexao:
        print("Erro ao conectar ao banco para obter admins.")
        return None

    cursor = conexao.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_usuario, nome_adm FROM admins")
        admins = cursor.fetchall()

        if not admins:
            return None

        # Cria uma inline keyboard com os botões dos admins
        markup = InlineKeyboardMarkup()
        for admin in admins:
            markup.add(
                InlineKeyboardButton(admin["nome_adm"], callback_data=f"adm_excluir_{admin['id_usuario']}")
            )
        return markup
    except Error as e:
        print(f"Erro ao executar consulta MySQL: {e}")
        return None
    finally:
        cursor.close()
        conexao.close()
def botoesConfirmarExlusao():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Sim", callback_data='adm_confirmar_exclusao'),
        InlineKeyboardButton("Não", callback_data='adm_cancelar_exclusao')
    )

    return markup