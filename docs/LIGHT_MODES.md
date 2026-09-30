# Catálogo de Efeitos - JBL PartyLight Stick & Beam

Este documento cataloga e descreve o comportamento visual dos modos de luz nativos das caixas JBL PartyLight Stick e Beam. Como não há documentação técnica detalhada fornecida pela JBL, as descrições baseiam-se em padrões da indústria de iluminação LED e engenharia reversa.

## Efeitos Compartilhados (Stick & Beam)

Estes são os efeitos básicos presentes em ambos os hardwares. Eles tendem a ser mais rítmicos e geométricos.

| ID | Nome PT-BR | Nome EN | Descrição Visual Esperada |
|----|------------|---------|---------------------------|
| 0x02 | **Neon** | NEON | Transições de cores suaves tipo fade, iluminando toda a área. Ideal para momentos contínuos de alta energia (Drop/Rave). |
| 0x09 | **Repetição** | LOOP | Efeito de "Chaser" (perseguição) onde a cor percorre o LED em ciclos contínuos (subindo, descendo ou girando). |
| 0x0A | **Salto** | BOUNCE | Blocos de luz ou pulsos que "quicam" de uma ponta à outra, ou do centro para as bordas. |
| 0x0B | **Ajuste** | TRIM | Comportamento similar a um VU Meter (equalizador), onde a barra de luz sobe e desce preenchendo o espaço de acordo com a intensidade do som. |
| 0x0C | **Mudança** | SWITCH | Cortes secos ("hard cuts") entre blocos de cores, sem transição suave. Excelente para strobo colorido ou batidas secas. |
| 0x0D | **Congelar** | FREEZE | Luzes estáticas, travadas na última cor/frame recebido. Não possui animação interna, funcionando como um canhão de luz fixa. |

---

## Efeitos Exclusivos (Apenas Stick)

A PartyLight Stick possui uma área de LEDs em formato de torre/bastão de 360 graus, permitindo animações de pixels muito mais complexas e orgânicas (simulação de física e natureza).

| ID | Nome PT-BR | Nome EN | Descrição Visual Esperada |
|----|------------|---------|---------------------------|
| 0x11 | **Aurora** | AURORA | Ondas lentas em gradiente simulando uma Aurora Boreal (geralmente tons de verde, azul e roxo), movimento muito suave e relaxante. |
| 0x12 | **Florada** | BLOSSOM | Pulsos de luz que começam no centro e se expandem suavemente para as pontas, lembrando o desabrochar de uma flor (rosas, púrpuras). |
| 0x10 | **Mar** | OCEAN | Ondulações contínuas de baixo para cima ou vice-versa em tons de azul e ciano. |
| 0x22 | **Céu** | SKY | Gradientes lentos e preenchimento total simulando variações do céu, possivelmente transições bem longas. |
| 0x19 | **Fogueira** | CAMPFIRE | Simulação de fogo! Cores quentes (vermelho, laranja, amarelo) oscilando ("flickering") na base e subindo gradativamente, imitando chamas. |
| 0x20 | **Tempestade** | STORM | Fundo geralmente mais escuro (nuvens) com flashes brancos intensos e aleatórios, reagindo rapidamente ao som. |
| 0x17 | **Relâmpago**| LIGHTNING | Similar a tempestade, mas com flashes estroboscópicos mais diretos e definidos (raios rasgando o bastão). |
| 0x1B | **Vagalume** | FIREFLY | Pontos isolados de luz verde/amarelada acendendo e apagando suavemente de forma caótica pelo bastão. |
| 0x1A | **Universo** | UNIVERSE | Cores profundas (azul marinho/roxo) com pontos piscantes ("twinkles") brilhantes simulando estrelas, movimento espacial lento. |
| 0x21 | **Flutuar** | HOVER | Bolhas de luz maiores subindo e descendo com física de gravidade suave. |
| 0x1F | **Cerveja** | BEER | Cores douradas/amarelas com pontinhos de luz subindo constantemente do chão para o topo, simulando o gás de um copo de cerveja. |
| 0x16 | **Gravidade** | GRAVITY | Blocos de luz ou "chuva de meteoros" que caem de cima para baixo constantemente (estilo Matrix). |
| 0x18 | **Falha** | GLITCH | Falhas visuais, ruídos aleatórios, separação forçada de canais RGB, transições caóticas sem padrão definido. |

---

## Observações de Controle

1. A cor desses modos é afetada pelos comandos de cor RGB. Em modos que possuem "cores obrigatórias" (como Cerveja, Fogueira, Universo), enviar uma cor manual pode re-tingir (tint) o efeito ou ser ignorado (precisa ser testado fisicamente).
2. A velocidade dos modos afeta o ritmo da animação interna.
3. Se a "Detecção de Som" (`AA 12 49 01 01`) estiver ativa, todos esses padrões tornam-se paramétricos à batida musical captada pelo microfone (ex: o Fogo pula quando dá um grave).
