from ibm_watson import AssistantV1
from bs4 import BeautifulSoup
from urllib.request import urlopen
import re

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
    return "" #re.search('\dh\s\d\dmin', info).group(0)

def format_nomes():
    nomes_formatados = ''
    for id_filme in filmes:
        nomes_formatados = nomes_formatados+'['+str(id_filme)+']: '+filmes[id_filme][0]+'\n'
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

assistant = AssistantV1(
        url='https://gateway.watsonplatform.net/assistant/api',
        iam_apikey='key',
        version='2019-02-28'
        )

workspace_id = 'af58982a-666e-467a-aadd-0218875c489d'

context = {}

userinput = ''

print("A aplicação mostrará os filmes em cartaz caso tenha interesse em saber.")
print("A cada filme será atribuído um número e você deverá referenciá-lo através desse número.")
print(" ")
print(" ")
print(" ")

while userinput != 'quit':
    #print(f"[{userinput}]")
    #print(type(userinput))
    load_filmes()
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


    print(result['output']['text'][0])
    userinput = input('>> ')