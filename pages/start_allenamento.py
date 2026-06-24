import flet as ft
import time
import threading
from datetime import datetime
from services.local_db import save_workout_local, get_local_workouts as get_workout_logs
from services.blockchain_db import store_workout_on_chain

def active_workout_view(page: ft.Page):

    scheda_source = page.session.store.get("workout_active_scheda")
    user_address  = page.session.store.get("user_address")
    private_key   = page.session.store.get("private_key")

    if not scheda_source:
        page.go("/workout")
        return ft.View("/live_workout", controls=[])

    # Recupero storico per i "ghost values" (valori suggeriti dall'ultimo allenamento)
    history_map = {}
    try:
        logs = get_workout_logs(user_address)
        if logs:
            for log in logs:
                for details in log.get("dettagli_esercizi", []):
                    clean_name = details.get("exercise_name", "").strip().lower()
                    if clean_name and clean_name not in history_map:
                        history_map[clean_name] = details.get("sets_performed", [])
    except Exception as e:
        print(f"Errore recupero storico ghost values: {e}")

    # --- TIMER ---
    start_time    = time.time()
    timer_running = True
    txt_timer = ft.Text("00:00", size=35, weight="bold", color=ft.Colors.CYAN_400,
                        font_family="Consolas, monospace")

    def update_timer():
        while timer_running:
            elapsed = int(time.time() - start_time)
            mins, secs = divmod(elapsed, 60)
            txt_timer.value = f"{mins:02d}:{secs:02d}"
            try:
                page.update()
            except Exception:
                break
            time.sleep(1)

    threading.Thread(target=update_timer, daemon=True).start()

    exercises_data = {}
    btn_termina = ft.ElevatedButton("TERMINA ALLENAMENTO",
                                    bgcolor=ft.Colors.RED_600, color="white",
                                    height=50, width=220)

    def show_snack(msg, color):
        snack = ft.SnackBar(ft.Text(msg, color="white", weight="bold"), bgcolor=color)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # -----------------------------------------------------------------------
    # FINE ALLENAMENTO: workflow completo Off-Chain → On-Chain
    # -----------------------------------------------------------------------
    def finish_workout(e):
        nonlocal timer_running

        btn_termina.text     = "SALVATAGGIO..."
        btn_termina.disabled = True
        btn_termina.bgcolor  = ft.Colors.GREY_700
        page.update()

        timer_running = False
        elapsed_seconds = int(time.time() - start_time)
        mins, secs = divmod(elapsed_seconds, 60)
        final_duration = f"{mins}m {secs}s"

        log_exercises = []
        for i, ex_original in enumerate(scheda_source.get("esercizi", [])):
            sets_done = []
            for row_refs in exercises_data.get(i, []):
                kg_val   = row_refs["kg"].current.value
                reps_val = row_refs["reps"].current.value
                if kg_val or reps_val:
                    sets_done.append({"kg": kg_val or "0", "reps": reps_val or "0"})
            log_exercises.append({
                "exercise_name": ex_original.get("exercise_name") or ex_original.get("nome"),
                "sets_performed": sets_done
            })

        workout_log = {
            "user_address": user_address,
            "type": "workout_log",
            "nome_scheda": scheda_source.get("nome_scheda"),
            "durata": final_duration,
            "data": datetime.now().strftime("%Y-%m-%d"),
            "dettagli_esercizi": log_exercises
        }

        try:
            # -----------------------------------------------------------
            # STEP 1 — Salvataggio locale (off-chain, GDPR compliant)
            # I dati sensibili (kg, reps) restano sul dispositivo.
            # -----------------------------------------------------------
            save_workout_local(user_address, workout_log)

            # -----------------------------------------------------------
            # STEP 2 — Notarizzazione on-chain (solo l'hash)
            # Lezione 5: firma con chiave privata → broadcast → conferma.
            # Se non c'è chiave privata (es. modalità demo) saltiamo
            # il passo on-chain senza bloccare l'utente.
            # -----------------------------------------------------------
            if private_key:
                tx_hash = store_workout_on_chain(user_address, private_key, workout_log)
                show_snack(f"⛓️ Allenamento notarizzato! TX: {tx_hash[:18]}...", "green")
            else:
                show_snack(f"✅ Allenamento salvato in locale ({final_duration}).", "green")
                print("⚠️  Nessuna chiave privata in sessione: step on-chain saltato.")

            page.go("/workout")

        except Exception as err:
            print(f"Errore durante il salvataggio: {err}")
            show_snack(f"❌ Errore: {str(err)}", "red")
            btn_termina.text     = "RIPROVA"
            btn_termina.disabled = False
            btn_termina.bgcolor  = ft.Colors.RED_600
            page.update()

    btn_termina.on_click = finish_workout

    # --- COSTRUZIONE UI ESERCIZI ---
    exercises_ui_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=25)

    for i, ex in enumerate(scheda_source.get("esercizi", [])):
        nome_ex      = ex.get("exercise_name") or ex.get("nome", "Esercizio")
        target_reps  = ex.get("ripetizioni", "8-10")
        clean_nome   = nome_ex.strip().lower()
        prev_sets    = history_map.get(clean_nome, [])

        sets_column = ft.Column(spacing=8)
        exercises_data[i] = []

        def add_set_row(e, ex_idx=i, container=sets_column,
                        default_target=target_reps, history_list=prev_sets):
            current_set_idx = len(exercises_data[ex_idx])
            display_num     = current_set_idx + 1

            ghost_kg, ghost_reps = "", ""
            if current_set_idx < len(history_list):
                prev_data = history_list[current_set_idx]
                # Recupero valori dallo storico
                val_kg, val_reps = "", ""
                if current_set_idx < len(history_list):
                    prev_data = history_list[current_set_idx]
                    
                    # Controllo rigoroso: prendiamo il valore SOLO se è un numero
                    raw_kg = str(prev_data.get("kg", ""))
                    raw_reps = str(prev_data.get("reps", ""))
                    
                    # Se la stringa non è numerica (es. "df"), la ignoriamo
                    val_kg = raw_kg if raw_kg.replace('.','',1).isdigit() else ""
                    val_reps = raw_reps if raw_reps.isdigit() else ""

            ref_kg   = ft.Ref[ft.TextField]()
            ref_reps = ft.Ref[ft.TextField]()

            def toggle_check(e):
                is_checked = e.control.icon == ft.Icons.CHECK_CIRCLE
                e.control.icon       = ft.Icons.RADIO_BUTTON_UNCHECKED if is_checked else ft.Icons.CHECK_CIRCLE
                e.control.icon_color = "grey" if is_checked else ft.Colors.GREEN_400
                row_container.bgcolor = "#1e293b" if is_checked else "#14532d"
                page.update()

            txt_kg = ft.TextField(
                ref=ref_kg, hint_text=ghost_kg or "Kg",
                hint_style=ft.TextStyle(color=ft.Colors.WHITE24),
                width=80, bgcolor=ft.Colors.BLACK12, border_radius=8,
                border_width=0, text_align="center",
                keyboard_type=ft.KeyboardType.NUMBER,
                text_style=ft.TextStyle(size=18, weight="bold", color="white")
            )
            txt_reps_field = ft.TextField(
                ref=ref_reps, hint_text=ghost_reps or default_target,
                hint_style=ft.TextStyle(color=ft.Colors.WHITE24),
                width=80, bgcolor=ft.Colors.BLACK12, border_radius=8,
                border_width=0, text_align="center",
                keyboard_type=ft.KeyboardType.NUMBER,
                text_style=ft.TextStyle(size=18, weight="bold", color="white")
            )

            row_container = ft.Container(
                content=ft.Row([
                    ft.Container(content=ft.Text(str(display_num), weight="bold", color="grey", size=16),
                                 width=30, alignment=ft.Alignment(0, 0)),
                    txt_kg,
                    txt_reps_field,
                    ft.IconButton(icon=ft.Icons.RADIO_BUTTON_UNCHECKED, icon_color="grey",
                                  tooltip="Segna come fatto", on_click=toggle_check),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_300,
                                  icon_size=20, tooltip="Rimuovi serie",
                                  on_click=lambda e, c=container: remove_last_set(c, ex_idx))
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                bgcolor="#1e293b", padding=10, border_radius=12,
                animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT)
            )

            exercises_data[ex_idx].append({"kg": ref_kg, "reps": ref_reps})
            container.controls.append(row_container)
            page.update()

        def remove_last_set(container, ex_idx):
            if container.controls:
                container.controls.pop()
                exercises_data[ex_idx].pop()
                page.update()

        try:
            num_series = int(ex.get("serie", 3))
        except Exception:
            num_series = 3

        for _ in range(num_series):
            add_set_row(None)

        last_log_str = "Primo Allenamento"
        if prev_sets:
            s1 = prev_sets[0]
            val_kg = str(s1.get('kg', '0'))
            if val_kg != "0":
                last_log_str = f"Ultimo: {val_kg}kg x {s1.get('reps','?')}"

        ex_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text(nome_ex, size=18, weight="bold", color="white"),
                        ft.Row([
                            ft.Container(content=ft.Text(f"Target: {target_reps}", size=11, weight="bold"),
                                         bgcolor=ft.Colors.BLUE_900, padding=4, border_radius=4),
                            ft.Text(last_log_str, color="grey", size=12, italic=True)
                        ])
                    ], spacing=3)
                ], alignment=ft.MainAxisAlignment.START),
                ft.Divider(color="transparent", height=10),
                ft.Row([
                    ft.Text("SET",  width=30, text_align="center", color="#64748b", size=11, weight="bold"),
                    ft.Text("KG",   width=80, text_align="center", color="#64748b", size=11, weight="bold"),
                    ft.Text("REPS", width=80, text_align="center", color="#64748b", size=11, weight="bold"),
                    ft.Text("FATTO",width=40, text_align="center", color="#64748b", size=11, weight="bold"),
                    ft.Container(width=40)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                sets_column,
                ft.Container(height=10),
                ft.TextButton(
                    "+ Aggiungi Serie", icon=ft.Icons.ADD, icon_color=ft.Colors.BLUE_400,
                    style=ft.ButtonStyle(color=ft.Colors.BLUE_400),
                    on_click=lambda e, i=i, c=sets_column: add_set_row(e, i, c)
                )
            ]),
            bgcolor="#0f172a", padding=15, border_radius=15,
            border=ft.Border.all(1, "#334155")
        )
        exercises_ui_list.controls.append(ex_card)

    header = ft.Container(
        content=ft.Column([
            ft.Text(scheda_source.get("nome_scheda", "Allenamento").upper(),
                    size=16, color="grey", weight="bold"),
            ft.Container(height=5),
            ft.Row([txt_timer], alignment=ft.MainAxisAlignment.CENTER),
        ]),
        padding=ft.Padding(bottom=20)
    )

    return ft.View(
        route="/live_workout",
        bgcolor="#0f172a",
        padding=ft.Padding(top=60, left=20, right=20, bottom=20),
        controls=[
            header,
            exercises_ui_list,
            ft.Container(height=10),
            ft.Container(content=btn_termina, alignment=ft.Alignment(0, 0), padding=20)
        ]
    )
