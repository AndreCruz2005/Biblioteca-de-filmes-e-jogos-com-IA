# Biblioteca de Filmes e Jogos com IA
Aplicação que permite ao usuário criar e gerenciar uma biblioteca pessoal de jogos e filmes com uso do modelo de IA generativa Gemini. Interface gráfica construída com a biblioteca PyQt5.

<a href="https://ibb.co/HtTVDk4"><img src="https://i.ibb.co/tqp4MWK/img-2025-01-13-22-58-32.png" alt="img-2025-01-13-22-58-32" border="0" /></a>

## Funcionalidades
Pesquisa de filmes usando a API do [TMDB](https://developer.themoviedb.org/reference/intro/authentication).

Pesquisa de jogos usando a API do [GiantBomb](https://www.giantbomb.com/api/).

Gerenciar as bibliotecas interagindo com a IA que é capaz de 5 comandos:
- Recomendar: Exibe jogos e filmes com base nas preferências do usuário
- Adicionar: Adicione jogose filme à biblioteca do usuário
- Classificar: Define a classificação de items da biblioteca com uma pontuação entre 0 e 10.
- Definir estado: Define o estado de um item da biblioteca como não jogado/não assistido, jogando/assistindo ou jogado/assistido
- Remover: Remove item da biblioteca

## Requisitos
- Versão mais recente de [Python](https://www.python.org/downloads/)
- Chave de API do [Gemini AI](https://aistudio.google.com/app/apikey)
- Chave de API do [TMDB](https://developer.themoviedb.org/reference/intro/authentication)
- Chave de API do [GiantBomb](https://www.giantbomb.com/api/)

**OBS:** Será necessário criar contas em cada uma das plataformas para conseguir uma chave de API.

## Uso
### Instalação
1. Clone o repositório
```
git clone https://github.com/AndreCruz2005/Biblioteca-de-filmes-e-jogos-com-IA/
```
2. No diretório do projeto, instale as dependências
```
pip install -r requirements.txt
```
### Execução
No diretório do projeto, execute o arquivo main.py no terminal
```
python main.py
```
### Configuração das chaves de API
Uma vez iniciada a aplicação, clique no ícone de engrenagem para exibir a aba de configurações, insira as chaves de API em seus respectivos campos (atente-se para não deixar espaços vazios em cada campo) e feche a aba de configurações clicando na engrenagem novamente.

### Interagindo com o modelo de IA
Digite seu comando na caixa de entrada no canto inferior direito da tela e envie clicando a tecla ENTER. Exemplos de comandos que você pode experimentar:
- Recomende jogos de ação
- Adicone Minecraft à minha biblioteca
- Coloque a nota de Minecraft como 10 e o estado como jogando.
- Adicione 3 jogos de sua escolha à minha biblioteca
- Remova todos os items da minha biblioteca

