from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from ibm_watson import AssistantV1, SpeechToTextV1, TextToSpeechV1
from bs4 import BeautifulSoup
from urllib.request import urlopen
import os
 

tts = TextToSpeechV1(
    iam_apikey = "key",
    url = "https://stream.watsonplatform.net/text-to-speech/api"
)

stt = SpeechToTextV1(
    iam_apikey='key',
    url='https://stream.watsonplatform.net/speech-to-text/api'
)


assistant = AssistantV1(
    url='https://gateway.watsonplatform.net/assistant/api',
    iam_apikey='key',
    version='2019-02-28'
)

workspace_id = 'af58982a-666e-467a-aadd-0218875c489d'

context = {}

numbers = {'um':'1', 'dois':'2', 'três':'3', 'quatro':'4', 'cinco':'5',  
           'seis':'6','sete':'7', 'oito':'8', 'nove':'9', 'dez':'10'}


filmes = {}

generos = ['Ação',
'Animação',
'Artes Marciais',
'Aventura',
'Biografia',
'Bollywood',
'Clássico',
'Comédia',
'Comédia dramática',
'Comédia Musical',
'Crime',
'Desenho Animado',
'Documentário',
'Doramas',
'Drama',
'Épico',
'Erótico',
'Espetáculo',
'Espionagem',
'Esporte',
'Experimental',
'Família',
'Fantasia',
'Faroeste',
'Ficção científica',
'Guerra',
'Histórico',
'Movie night',
'Musical',
'Ópera',
'Outros',
'Policial', 
'Romance',
'Show',
'Suspense',
'Terror']

def get_generos(metabody):
    text = metabody.get_text()
    return [x for x in generos if x in text]

def get_elenco_formatado(word):
    words = word.split(',')
    result = ''
    for w in words:
        result+=w.strip()+', '
    return result[0:-2]

def format_rating(rating):
    base = rating.replace(' ', '')
    return base[0:8] + ': ' + rating[8:12] +' - '+ rating[13:21] + ': ' + rating[21:25] + ' - ' + rating[25:36] + ': ' + rating[36:]
    
def get_duracao(info):
    return "120 minutos"
    
def format_nomes():
    nomes_formatados = ''
    for id_filme in filmes:
        nomes_formatados = nomes_formatados+'[Filme número '+str(id_filme)+']: '+filmes[id_filme][0]+', \n'
    return nomes_formatados

def load_filmes():
    
    if (not filmes):
        html_doc = urlopen('http://www.adorocinema.com/filmes/numero-cinemas/').read()
    
        soup = BeautifulSoup(html_doc, 'html.parser')
        filme = []
        id_filme = 1
    
        for mdl in soup.find_all('li',class_='mdl'):
            nomeFilme = mdl.find('h2', class_='meta-title').find('a', class_='meta-title-link').text.strip()
            metabody = mdl.find('div', class_='meta-body-info')
            duracao = get_duracao(metabody.get_text())
            data_em_cartaz = metabody.find('span', class_='date').text.strip()
            genero = get_generos(metabody)
            diretor = mdl.find('div', class_='meta-body-direction').find('a', class_='blue-link').text.strip()
            elenco = get_elenco_formatado(mdl.find('div', class_='meta-body-actor').get_text().replace('Elenco:','').replace('\n', '').strip())
            sinopse = mdl.find('div', class_='synopsis').get_text().strip()
            classificacao=format_rating(mdl.find('div', class_='rating-holder').get_text().replace('\n','').strip())
            filme = [nomeFilme, duracao, data_em_cartaz, genero, diretor, elenco, 
                     sinopse, classificacao]
            filmes[id_filme]=filme
            id_filme += 1
            if (id_filme == 11):
                break
        
    return filmes

def do_action(action, index, context_variable):
    params = action['parameters']
    filme = filmes[params['filme']]
    data = {
        context_variable : filme[0]+' - '+filme[index],
    }
    return data

def start(bot, update):
    user_id = update.message.chat_id
    first_name = update['message']['chat']['first_name']
    message_text = f"Olá, {first_name}!"
    send_voice(bot, user_id, message_text)

def talk(bot, update):
    
    user_id = update['message']['chat']['id']
    file_name = str(user_id) + '_' + str(update.message.from_user.id) + str(update.message.message_id) + '.ogg'
    voice = update['message']['voice']
    voice.get_file().download(file_name)

    print("reconhecendo")
    
    with open(file_name, 'rb') as audio_file:
        message_text = stt.recognize(
                   audio=audio_file,
                   content_type='audio/ogg',
                   model='pt-BR_NarrowbandModel'
               ).get_result()

    os.remove(file_name)

    text = message_text['results'][0]['alternatives'][0]['transcript']
    
    print(f"Você disse {text}")
    print("respondendo")
    reply = chat(text)
    print(reply)
    
    send_voice(bot, user_id, reply)
    
def send_voice(bot, chat_id, text):
    
    print("tts")
    with open('audio.ogg', 'wb') as audio_file:
        content = tts.synthesize(
                text,
                voice='pt-BR_IsabelaVoice',
                accept='audio/ogg'
        ).get_result().content
        audio_file.write(content)
    bot.send_voice(chat_id=chat_id, voice=open('audio.ogg', 'rb'))
    print("voice sent")
    os.remove('audio.ogg')

def normalize(text):

    stripped_text = text.strip()
    
    if (stripped_text in numbers):
        return numbers[stripped_text]
    
    return text
    
def main():
    print("init")

    global context
    context = {}

    load_filmes()
        
    updater = Updater('936295833:AAHPfZXeYKt0f-P5IF119i33AR01poigFkQ') #, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start',start))
    dp.add_handler(MessageHandler(Filters.voice, talk))
    updater.start_polling()
    updater.idle()

def chat(userinput):

    userinput = normalize(userinput)
    print(f"Input: {userinput}")
    
    global context
    
    response = assistant.message(
            workspace_id=workspace_id,
            input={
                    'text': userinput
                    },
                    context=context)
    
    result = response.get_result()
    context = result['context']
    data = {}
    if 'actions' in result:
        action = result['actions'][0]
        if (action['name'] == 'CheckMovies'):
            data = {
                    'filmes': format_nomes(),
                    }
        elif (action['name'] == 'GetSynopsis'):
            data = do_action(action, 6, 'sinopse')
        elif (action['name'] == 'GetActors'):
            data = do_action(action, 5, 'elenco')
        elif (action['name'] == 'GetDirector'):
            data = do_action(action, 4, 'diretor')
        elif (action['name'] == 'GetRating'):
            data = do_action(action, 7, 'classificacao')
        elif (action['name'] == 'GetLength'):
            data = do_action(action, 1, 'duracao')
        context[action['result_variable']] = data
        result = assistant.message(
                workspace_id=workspace_id,
                input={
                        'text': ''
                },
                context=context).get_result()
        context = result['context']


    return result['output']['text'][0]
        

if __name__ == '__main__':
    main()



