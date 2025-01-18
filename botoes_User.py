from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton



def botoesMenuUser():
    markup = InlineKeyboardMarkup()


    markup.row(
        InlineKeyboardButton("👤 Meu Perfil", callback_data="menu_meu_perfil"),
        InlineKeyboardButton("🆘 Suporte", url= 'https://pt.wikipedia.org/wiki/Programa_Ol%C3%A1_Mundo')
    )

    markup.row(
        InlineKeyboardButton("ℹ Informações", url='https://t.me/BravusList'),
        InlineKeyboardButton("📕 Regras", callback_data="menu_regras")
    )

    markup.add(
        InlineKeyboardButton('Adicionar', callback_data='menu_add')
    )

    return markup



def botaoRegras():
    markup = InlineKeyboardMarkup()

    markup.add(
        InlineKeyboardButton("🏠 Início", callback_data='menu_inicio')
    )
    return markup

def botaoMeuPerfil():
    markup = InlineKeyboardMarkup()
    # Adicionar lógica de botões aqui, caso haja
    markup.add(
        InlineKeyboardButton("🏠 Início", callback_data='menu_inicio')
    )
    return markup


def botoesAdicaoCanalouGrupo():
    markup = InlineKeyboardMarkup()

    markup.row(
        InlineKeyboardButton("Adicionar Grupo 👥", url='http://t.me/BravusListBot?startgroup&admin=delete_messages+invite_users+pin_messages'),
        InlineKeyboardButton("Adicionar Canal 📢", url='http://t.me/BravusListBot?startchannel&admin=post_messages+edit_messages+delete_messages+invite_users+pin_messages+manager_chat')
    )

    # Adicionando o botão "🏠 Início"
    markup.add(
        InlineKeyboardButton("🏠 Início", callback_data='menu_inicio')
    )

    return markup