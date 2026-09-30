import sqlite3
import os

DB_PATH = 'faria_fx.db'

def main():
    if not os.path.exists(DB_PATH):
        print("Database not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create beat_pos column if it doesn't exist
    cursor.execute("PRAGMA table_info(events)")
    columns = [c[1] for c in cursor.fetchall()]
    if "beat_pos" not in columns:
        print("Adicionando coluna beat_pos no banco de dados...")
        cursor.execute("ALTER TABLE events ADD COLUMN beat_pos REAL DEFAULT 0.0")
        conn.commit()

    cursor.execute("SELECT id, current_filename FROM tracks")
    tracks = cursor.fetchall()

    if not tracks:
        print("Nenhuma track encontrada.")
        return

    for track_id, filename in tracks:
        print(f"\n--- Migrando Track: {filename} ---")
        bpm_input = input("Digite o BPM (ou deixe em branco para ignorar essa track): ")
        if not bpm_input.strip():
            continue
            
        try:
            bpm = float(bpm_input)
        except ValueError:
            print("BPM invalido.")
            continue
            
        cursor.execute("SELECT id, time_ms, preset FROM events WHERE track_id = ?", (track_id,))
        events = cursor.fetchall()
        
        if not events:
            print("Nenhum cue encontrado.")
            continue
            
        print("\nAqui estao os primeiros cues:")
        for i, ev in enumerate(events[:5]):
            print(f"[{i}] Tempo: {ev[1]}ms - {ev[2]}")
            
        ancora_idx = input("\nEscolha o indice do cue para usar como ancora (ex: 0) ou deixe em branco para usar o inicio absoluto (0ms = Bar 1.1): ")
        
        offset_ms = 0.0
        
        if ancora_idx.strip():
            try:
                idx = int(ancora_idx)
                if 0 <= idx < len(events):
                    ancora_ev = events[idx]
                    ancora_ms = ancora_ev[1]
                    bar_input = input(f"O cue {ancora_ms}ms corresponde a qual Bar.Beat no VDJ? (ex: 17.1): ")
                    
                    parts = bar_input.split('.')
                    if len(parts) >= 2:
                        bar = int(parts[0])
                        b = int(parts[1])
                        target_beat = ((bar - 1) * 4) + (b - 1)
                        
                        beats_per_ms = bpm / 60000.0
                        ms_to_cover = target_beat / beats_per_ms
                        
                        offset_ms = ancora_ms - ms_to_cover
                        print(f"Calculado grid offset da track: {offset_ms:.2f}ms")
                    else:
                        print("Formato invalido. Usando offset 0.")
            except:
                print("Erro ao processar ancora. Usando offset 0.")
                
        beats_per_ms = bpm / 60000.0
        for ev in events:
            ev_id = ev[0]
            ev_time = ev[1]
            
            beat_pos = (ev_time - offset_ms) * beats_per_ms
            if beat_pos < 0: beat_pos = 0.0
            
            cursor.execute("UPDATE events SET beat_pos = ? WHERE id = ?", (beat_pos, ev_id))
            
        conn.commit()
        print(f"Atualizados {len(events)} cues para a track!")
        
    conn.close()
    print("\nMigracao finalizada! Lembre-se de reiniciar o servidor (run_web.py).")

if __name__ == "__main__":
    main()
