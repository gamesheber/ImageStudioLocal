# Image Studio Local

Aplicativo Android para edição de imagens de moda/catálogo usando Hugging Face Inference Providers.

## O que já está incluído

- Foto principal da modelo
- Foto de referência da roupa
- Prompt editável
- 9:16, 1:1 e 16:9
- Geração por IA
- Pré-visualização
- Exportação para `Pictures/ImageStudioLocal`
- Interface escura adaptada para celular
- Build automático de APK pelo GitHub Actions

## Importante

Este projeto usa Qwen/Qwen-Image-Edit pela infraestrutura de inferência do Hugging Face. O modelo não é baixado para o celular. Isso evita o problema de tentar colocar um modelo de dezenas de GB no Moto G75.

O projeto monta a foto da modelo e a referência da roupa em uma imagem de duas áreas e instrui o modelo sobre o papel de cada lado. Isso é uma solução de compatibilidade; não existe garantia de cópia pixel-a-pixel da roupa.

O token do Hugging Face é pedido dentro do app e não é enviado para este projeto ou para outro servidor. Ele é usado diretamente na chamada de inferência.

## Como gerar o APK

1. Crie um repositório no GitHub.
2. Envie todos os arquivos desta pasta mantendo a pasta `.github/workflows`.
3. Abra a aba `Actions`.
4. Execute `Build Image Studio Local`.
5. Quando terminar, abra o artefato `ImageStudioLocal-debug`.
6. Baixe o APK e instale no Android.

## Token

Crie um token no Hugging Face em Settings > Access Tokens e use um token com permissão de inferência compatível com sua conta.

O serviço de inferência pode ter limites/créditos/custos conforme a conta e o provedor selecionado. Este aplicativo não torna a geração ilimitada.

## Segurança

Use apenas imagens de pessoas adultas e conteúdo de moda/catálogo. Não use o aplicativo para gerar nudez sexual explícita ou conteúdo sexual envolvendo menores.
