import argparse
import json
import re
from pathlib import Path


KNOWN_MODES = {
    0x02: "Modo 0x02",
    0x08: "Modo 0x08",
    0x09: "Modo 0x09",
    0x0A: "Modo 0x0A",
    0x0B: "Modo 0x0B",
    0x0C: "Modo 0x0C",
    0x0D: "Modo 0x0D",
    0x10: "Modo 0x10",
    0x11: "Modo 0x11",
    0x12: "Modo 0x12",
    0x16: "Gravidade (Gravity)",
    0x17: "Relâmpago (Lightning)",
    0x18: "Falha (Glitch)",
    0x19: "Modo 0x19",
    0x1A: "Modo 0x1A",
    0x1B: "Modo 0x1B",
    0x1F: "Modo 0x1F",
    0x20: "Modo 0x20",
    0x21: "Modo 0x21",
    0x22: "Modo 0x22",
}

TAG_NAMES_32 = {
    0x31: "Modo Ativo",
    0x32: "Cor Base RGB",
    0x36: "Switch de Efeito",
    0x45: "Brilho Master",
    0x46: "Velocidade / Intensidade",
    0x47: "Parâmetro 0x47",
    0x48: "Parâmetro 0x48",
    0x49: "Luz Traseira",
    0x4A: "Tabela de Modos Suportados",
}

TAG_NAMES_12 = {
    0x31: "Model ID",
    0x32: "Parâmetro 0x32",
    0x37: "Endereço MAC",
    0x3C: "Parâmetro 0x3C",
    0x40: "Número de Série",
    0x41: "Versão de Firmware",
    0x45: "Detecção de Som",
    0x4A: "Parâmetro 0x4A",
}


def parse_tlvs(data: bytes, msg_type: int):
    """
    Decodifica a stream TLV a partir do offset 4 (após AA, Opcode, Length Low, Length High).
    """
    if len(data) < 4:
        return {}

    tlvs = {}
    idx = 4
    while idx < len(data):
        tag = data[idx]
        if idx + 1 >= len(data):
            break
        tlen = data[idx + 1]
        val = data[idx + 2 : idx + 2 + tlen]

        tag_name_map = TAG_NAMES_32 if msg_type == 0x32 else TAG_NAMES_12
        field_name = tag_name_map.get(tag, f"Desconhecido (0x{tag:02x})")

        formatted_val = format_tlv_value(tag, val, msg_type)

        tlvs[f"0x{tag:02x}"] = {
            "tag": tag,
            "name": field_name,
            "len": tlen,
            "raw_hex": val.hex(" "),
            "formatted": formatted_val,
        }
        idx += 2 + tlen

    return tlvs


def format_tlv_value(tag: int, val: bytes, msg_type: int) -> str:
    if msg_type == 0x32:
        if tag == 0x31 and len(val) == 1:
            mode_id = val[0]
            mode_name = KNOWN_MODES.get(mode_id, "Desconhecido")
            return f"0x{mode_id:02x} ({mode_name})"
        elif tag == 0x32 and len(val) == 3:
            r, g, b = val[0], val[1], val[2]
            return f"RGB({r}, {g}, {b}) / #{val.hex().upper()}"
        elif tag == 0x45 and len(val) == 1:
            dec_pct = val[0]
            return f"{dec_pct}% (0x{val[0]:02x})"
        elif tag == 0x46 and len(val) == 1:
            return f"{val[0]} (0x{val[0]:02x})"
        elif tag == 0x49 and len(val) == 1:
            return "Ligada" if val[0] == 1 else "Desligada" if val[0] == 0 else f"0x{val[0]:02x}"
        elif tag == 0x36 and len(val) == 1:
            return "Ativo (1)" if val[0] == 1 else "Inativo (0)" if val[0] == 0 else f"0x{val[0]:02x}"
        elif tag == 0x4A:
            return f"{len(val)} modos: {val.hex(' ')}"
    elif msg_type == 0x12:
        if tag == 0x37 and len(val) == 6:
            return ":".join(f"{b:02X}" for b in val)
        elif tag == 0x40:
            try:
                return val.decode("ascii", errors="replace").strip()
            except Exception:
                return val.hex(" ")
        elif tag == 0x41 and len(val) == 3:
            return f"v{val[0]}.{val[1]}.{val[2]}"
        elif tag == 0x45 and len(val) == 1:
            return "Ligada" if val[0] == 1 else "Desligada" if val[0] == 0 else f"0x{val[0]:02x}"

    return val.hex(" ")


def extract_packets(text):
    packets = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        match = re.search(r"(aa(?:\s+[0-9a-fA-F]{2}){4,})", line, re.I)
        if not match:
            continue

        try:
            data = bytes.fromhex(match.group(1))
        except ValueError:
            continue

        if len(data) < 4:
            continue

        packet_type = data[1]
        payload_len = data[2] | (data[3] << 8) if len(data) >= 4 else None

        tlvs = parse_tlvs(data, packet_type)

        packets.append(
            {
                "line": line_no,
                "type": packet_type,
                "payload_len": payload_len,
                "data": data,
                "hex": data.hex(" "),
                "tlvs": tlvs,
            }
        )

    return packets


def extract_actions(text):
    actions = []
    lines = text.splitlines()

    for i, line in enumerate(lines):
        if "=== AÇÃO DO USUÁRIO ===" not in line:
            continue

        device_type = None
        action = None

        for following in lines[i + 1 : i + 8]:
            if following.startswith("TIPO:"):
                device_type = following.split(":", 1)[1].strip()
            elif following.startswith("AÇÃO:"):
                action = following.split(":", 1)[1].strip()

        actions.append(
            {
                "line": i + 1,
                "device_type": device_type,
                "action": action,
            }
        )

    return actions


def compare_tlvs(prev_tlvs, curr_tlvs):
    changes = []
    all_tags = sorted(list(set(list(prev_tlvs.keys()) + list(curr_tlvs.keys()))))

    for tag in all_tags:
        old = prev_tlvs.get(tag)
        new = curr_tlvs.get(tag)

        if old is None or new is None:
            changes.append(
                {
                    "tag": tag,
                    "name": (old or new)["name"],
                    "old": None if old is None else old["formatted"],
                    "new": None if new is None else new["formatted"],
                    "raw_old": None if old is None else old["raw_hex"],
                    "raw_new": None if new is None else new["raw_hex"],
                }
            )
        elif old["raw_hex"] != new["raw_hex"]:
            changes.append(
                {
                    "tag": tag,
                    "name": new["name"],
                    "old": old["formatted"],
                    "new": new["formatted"],
                    "raw_old": old["raw_hex"],
                    "raw_new": new["raw_hex"],
                }
            )

    return changes


def analyze(text):
    packets = extract_packets(text)
    actions = extract_actions(text)

    states_32 = [p for p in packets if p["type"] == 0x32]
    states_12 = [p for p in packets if p["type"] == 0x12]

    comparisons_32 = []
    for index in range(1, len(states_32)):
        prev = states_32[index - 1]
        curr = states_32[index]
        diff = compare_tlvs(prev["tlvs"], curr["tlvs"])
        if diff:
            comparisons_32.append(
                {
                    "from_line": prev["line"],
                    "to_line": curr["line"],
                    "changes": diff,
                }
            )

    comparisons_12 = []
    for index in range(1, len(states_12)):
        prev = states_12[index - 1]
        curr = states_12[index]
        diff = compare_tlvs(prev["tlvs"], curr["tlvs"])
        if diff:
            comparisons_12.append(
                {
                    "from_line": prev["line"],
                    "to_line": curr["line"],
                    "changes": diff,
                }
            )

    return {
        "packet_count": len(packets),
        "state_packet_count": len(states_32),
        "info_packet_count": len(states_12),
        "action_count": len(actions),
        "actions": actions,
        "state_changes_32": comparisons_32,
        "info_changes_12": comparisons_12,
    }


def print_report(result):
    print("=" * 70)
    print("JBL BLE CAPTURE ANALYZER (TLV Parser)")
    print("=" * 70)
    print()

    print(f"Pacotes encontrados: {result['packet_count']}")
    print(f"Pacotes de Estado (0x32): {result['state_packet_count']}")
    print(f"Pacotes de Identidade (0x12): {result['info_packet_count']}")
    print(f"Ações anotadas: {result['action_count']}")
    print()

    if result["actions"]:
        print("AÇÕES ANOTADAS")
        print("-" * 70)
        for action in result["actions"]:
            print(
                f"Linha {action['line']}: "
                f"[{action['device_type'] or '?'}] -> "
                f"{action['action'] or '?'}"
            )
        print()

    print("ALTERAÇÕES DE ESTADO DE ILUMINAÇÃO (0x32)")
    print("-" * 70)
    if not result["state_changes_32"]:
        print("Nenhuma alteração entre pacotes 0x32 foi detectada.")
    else:
        for num, comp in enumerate(result["state_changes_32"], start=1):
            print(f"\n#{num}  (Linha {comp['from_line']} -> {comp['to_line']}):")
            for c in comp["changes"]:
                print(f"  • {c['name']} ({c['tag']}): {c['old']}  -->  {c['new']}")

    if result["info_changes_12"]:
        print()
        print("ALTERAÇÕES DE METADADOS / IDENTIDADE (0x12)")
        print("-" * 70)
        for num, comp in enumerate(result["info_changes_12"], start=1):
            print(f"\n#{num}  (Linha {comp['from_line']} -> {comp['to_line']}):")
            for c in comp["changes"]:
                print(f"  • {c['name']} ({c['tag']}): {c['old']}  -->  {c['new']}")


def main():
    parser = argparse.ArgumentParser(
        description="Analisa capturas de BLE do JBL Controller com decodificação TLV."
    )
    parser.add_argument(
        "capture",
        type=Path,
        help="Arquivo de captura .txt gerado pelo ble_probe.py",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Gera o resultado em JSON em vez do relatório humano.",
    )

    args = parser.parse_args()

    if not args.capture.exists():
        raise SystemExit(f"Arquivo não encontrado: {args.capture}")

    text = args.capture.read_text(encoding="utf-8", errors="replace")
    result = analyze(text)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_report(result)


if __name__ == "__main__":
    main()
