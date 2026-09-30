# Catálogo de Efeitos - JBL PartyLight Stick e Beam

Mapeamento dos modos de animação disponíveis no firmware dos dispositivos JBL PartyLight Stick e JBL PartyLight Beam.

---

## 1. Efeitos suportados por ambos os modelos (Stick e Beam)

Estes modos estão presentes tanto na lista do PartyLight Stick quanto na lista do PartyLight Beam (campo `0x4A` de `AA 32`):

| ID (Hex) | Nome (APK) | Nome exibido na interface | Comportamento visual observado |
|---|---|---|---|
| `0x02` | NEON | Neon | Transição suave e contínua de cores em gradiente. |
| `0x09` | LOOP | Repetição | Movimento cíclico de luz percorrendo o dispositivo. |
| `0x0A` | BOUNCE | Salto | Pulso de luz que rebate entre as extremidades. |
| `0x0B` | TRIM | Ajuste | Animação em barra preenchida em estilo medidor VU. |
| `0x0C` | SWITCH | Mudança | Alternância rápida e direta entre blocos de cor sem fade. |
| `0x0D` | FREEZE | Congelar | Luz estática na última cor configurada, sem movimento. |

---

## 2. Efeitos exclusivos do PartyLight Stick

Devido à disposição linear de LEDs em torre (360 graus), o PartyLight Stick suporta animações que dependem de resolução espacial vertical:

| ID (Hex) | Nome (APK) | Nome exibido na interface | Comportamento visual |
|---|---|---|---|
| `0x15` | STATIC | Cor Sólida | Iluminação uniforme em todo o bastão. Requer `PatternLooping = 0x01` (`0x36`). Não suportado pelo Beam. |
| `0x10` | OCEAN | Mar | Movimento ondulatório lento em tons frios. |
| `0x11` | AURORA | Aurora | Gradiente lento vertical simulando aurora boreal. |
| `0x12` | BLOSSOM | Florada | Expansão de luz a partir da região central para as pontas. |
| `0x16` | GRAVITY | Gravidade | Blocos de luz descendo continuamente em cascata. |
| `0x17` | LIGHTNING | Relâmpago | Flashes estroboscópicos de alta intensidade em intervalos irregulares. |
| `0x18` | GLITCH | Falha | Padrão visual irregular com cortes rápidos. |
| `0x19` | CAMPFIRE | Fogueira | Simulação de chamas oscilando a partir da base do bastão. |
| `0x1A` | UNIVERSE | Universo | Pontos de brilho intermitente sobre fundo escuro. |
| `0x1B` | FIREFLY | Vagalume | Pontos individuais acesos em posições aleatórias. |
| `0x1F` | BEER | Cerveja | Pontos de luz subindo da base simulando efervescência. |
| `0x20` | STORM | Tempestade | Fundo escuro com relâmpagos intermitentes. |
| `0x21` | HOVER | Flutuar | Blocos luminosos oscilando com aceleração e desaceleração. |
| `0x22` | SKY | Céu | Transições graduais entre tons de azul e branco. |

---

## 3. Observações operacionais

1. **Interação com comandos de cor RGB (`0x32`):**
   - Na maioria dos modos dinâmicos (como `NEON`, `LOOP`, `BOUNCE`), a cor base enviada redefine a paleta de cores dominante da animação.
   - Em modos temáticos (como `CAMPFIRE` ou `BEER`), a alteração de cor pode ser parcialmente mesclada com a animação de fábrica ou ignorada pelo firmware.
2. **Interação com a velocidade (`0x46`):**
   - O valor de velocidade (`0x00` a `0x64`) acelera ou desacelera a taxa de atualização da animação interna.
3. **Reação ao som (`AA 13` / `0x45 01 01`):**
   - Quando ativada, a animação selecionada passa a modular sua intensidade e pulso de acordo com os sinais captados pelo microfone embutido no hardware.
