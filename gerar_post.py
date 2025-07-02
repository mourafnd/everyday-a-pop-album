# gerar_post.py - Gera um post diário com um álbum pop

from openai import OpenAI
from datetime import datetime
import os
import re
import unicodedata

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Função para gerar slug a partir de texto
def gerar_slug(texto):
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('utf-8')
    texto = re.sub(r'[^a-zA-Z0-9\s-]', '', texto)
    texto = texto.lower().replace(' ', '-').strip('-')
    return texto

# Gera conteúdo e valida presença de título/autor

def gerar_conteudo(max_tentativas=3):
    prompt = (
        "Recomende um álbum pop (brasileiro, latino ou internacional) para hoje.\n"
        "Comece exatamente com o nome do álbum em negrito, seguido por 'by' e o artista em negrito, no formato:\n"
        "**Album Name** by **Artist Name**\n\n"
        "Depois, escreva os seguintes tópicos:\n"
        "- Year\n"
        "- Country\n"
        "- Genre\n"
        "- Main Tracks (5 a 8 faixas)\n"
        "- One or two curiosities and any other information about this album that you might find useful.\n"
        "- Suggest streaming links (Spotify, YouTube, etc. - use names only)\n"
        "Escreva em inglês e use títulos destacados (bold ou emojis)."
    )

    for tentativa in range(1, max_tentativas + 1):
        resposta = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        conteudo = resposta.choices[0].message.content.strip()

        titulo_match = re.search(r"\*\*(.*?)\*\* by \*\*(.*?)\*\*", conteudo)
        if titulo_match:
            return conteudo

        print(f"Tentativa {tentativa} falhou em extrair título corretamente")

    raise ValueError("Falha ao obter nome do álbum e artista após várias tentativas.")

# Salvar conteúdo como arquivo Markdown
def salvar_post(conteudo, hoje):
    titulo_match = re.search(r'\*\*(.*?)\*\* by \*\*(.*?)\*\*', conteudo)
    if not titulo_match:
        raise ValueError("Formato de título inválido: conteúdo não será salvo.")

    album = titulo_match.group(1).strip()
    artista = titulo_match.group(2).strip()

    titulo = f"{album} - {artista}"
    slug = gerar_slug(f"{album} {artista}")
    descricao = f"Discover the album '{album}' by {artista}, a highlight in pop music."
    keywords = f"pop album, {artista}, {album}, music"

    caminho = f"content/posts/{slug}.md"
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(f"title: \"{titulo}\"\n")
        f.write(f"date: {hoje.isoformat()}\n")
        f.write(f"slug: \"{slug}\"\n")
        f.write(f"description: \"{descricao}\"\n")
        keywords_formatadas = ', '.join([f'\"{k.strip()}\"' for k in keywords.split(',')])
        f.write(f"keywords: [{keywords_formatadas}]\n")
        f.write("---\n\n")
        f.write(conteudo)

# Executar geração
if __name__ == "__main__":
    hoje = datetime.now()
    conteudo = gerar_conteudo()
    salvar_post(conteudo, hoje)
    print("Post gerado com sucesso!")
