import flet as ft
import uuid
import os
import json
from datetime import datetime
from services.local_db import save_workout_local
from services.blockchain_db import store_workout_on_chain

def create_routine_view(page: ft.Page):
    # Usiamo il wallet address come identificatore (non più l'email)
    user_address = page.session.store.get("user_address") or "atleta.gymlog@test.com"
    private_key  = page.session.store.get("private_key")

    # --- CONTROLLO MODALITÀ MODIFICA ---
    scheda_da_modificare = page.session.store.get("scheda_edit")
    is_editing = scheda_da_modificare is not None
    exercises_buffer = scheda_da_modificare.get("esercizi", []) if is_editing else []

    # Catalogo esercizi (locale)
    lista_esercizi_db = ["Panca Piana", "Squat", "Stacco da terra", "Trazioni", "Lento Avanti", "Bicipiti Bilanciere"]
    if os.path.exists("local_data/custom_esercizi.json"):
        try:
            with open("local_data/custom_esercizi.json", "r") as f:
                for ex in json.load(f):
                    lista_esercizi_db.append(ex.get("exercise_name"))
        except Exception:
            pass

    options_list = [ft.dropdown.Option(ex) for ex in lista_esercizi_db]

    # --- HELPER UI ---
    def show_snack(msg, color):
        snack = ft.SnackBar(ft.Text(msg, color="white", weight="bold"), bgcolor=color)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def styled_textfield(label, hint_text, initial_value=""):
        return ft.Column([
            ft.Text(label.upper(), size=12, weight=ft.FontWeight.BOLD, color="#94a3b8"),
            ft.TextField(
                value=initial_value,
                hint_text=hint_text,
                border_radius=12,
                bgcolor="#1e293b",
                border_color="#334155",
                text_style=ft.TextStyle(color="white"),
                hint_style=ft.TextStyle(color="#64748b"),
                content_padding=15,
                cursor_color=ft.Colors.BLUE_400
            )
        ], spacing=5)

    # Pre-compilazione campi se in modifica
    init_nome  = scheda_da_modificare.get("nome_scheda", "") if is_editing else ""
    init_split = scheda_da_modificare.get("split_type",  "") if is_editing else ""

    txt_nome  = styled_textfield("Nome Scheda", "Es. Giorno 1", init_nome)
    txt_split = styled_textfield("Tipo Split",  "Es. Push, Pull, A, B...", init_split)

    lbl_esercizi_count = ft.Text(f"ESERCIZI ({len(exercises_buffer)})", size=12, weight="bold", color="#94a3b8")
    exercises_column = ft.Column(spacing=10)

    # --- DIALOG AGGIUNTA ESERCIZIO ---
    dd_exist      = ft.Dropdown(label="Seleziona Esistente", options=options_list,
                                bgcolor="#1e293b", border_color="#334155", color="white", width=250)
    txt_new_custom = ft.TextField(label="Oppure nome nuovo...", bgcolor="#1e293b",
                                  border_color="#334155", color="white", visible=False, width=250)
    sw_custom = ft.Switch(label="Nuovo Esercizio Personalizzato", value=False, active_color=ft.Colors.BLUE_400)
    txt_sets  = ft.TextField(label="Serie", width=100, bgcolor="#1e293b", border_color="#334155", color="white", value="3")
    txt_reps  = ft.TextField(label="Reps",  width=100, bgcolor="#1e293b", border_color="#334155", color="white", value="10")

    def toggle_custom_exercise(e):
        dd_exist.visible       = not sw_custom.value
        txt_new_custom.visible = sw_custom.value
        page.update()

    def confirm_add_exercise(e):
        ex_name = txt_new_custom.value if sw_custom.value else dd_exist.value
        if not ex_name:
            show_snack("Devi inserire o selezionare un nome!", "red")
            return

        if sw_custom.value:
            new_custom_ex = {"id": str(uuid.uuid4()), "exercise_name": ex_name, "user_address": user_address}
            os.makedirs("local_data", exist_ok=True)
            saved_customs = []
            if os.path.exists("local_data/custom_esercizi.json"):
                try:
                    with open("local_data/custom_esercizi.json", "r") as f:
                        saved_customs = json.load(f)
                except Exception:
                    pass
            saved_customs.append(new_custom_ex)
            with open("local_data/custom_esercizi.json", "w") as f:
                json.dump(saved_customs, f)
            dd_exist.options.append(ft.dropdown.Option(ex_name))

        exercises_buffer.append({
            "id": str(uuid.uuid4())[:8],
            "user_address": user_address,
            "type": "esercizio_catalogo",
            "exercise_name": ex_name,
            "serie": txt_sets.value,
            "ripetizioni": txt_reps.value,
            "is_custom": sw_custom.value,
            "note_ai": "Aggiunto manualmente"
        })
        update_exercises_list()

        dialog_add.open = False
        txt_new_custom.value = ""
        dd_exist.value = None
        sw_custom.value = False
        toggle_custom_exercise(None)

    def close_dialog(e=None):
        dialog_add.open = False
        sw_custom.value = False
        toggle_custom_exercise(None)
        page.update()

    dialog_add = ft.AlertDialog(
        title=ft.Text("Aggiungi Esercizio"), bgcolor="#0f172a",
        content=ft.Column([sw_custom, dd_exist, txt_new_custom, ft.Row([txt_sets, txt_reps])], height=200, tight=True),
        actions=[
            ft.TextButton("Annulla", on_click=close_dialog),
            ft.ElevatedButton("Aggiungi", on_click=confirm_add_exercise, bgcolor=ft.Colors.BLUE_600, color="white")
        ],
    )
    sw_custom.on_change = toggle_custom_exercise

    def open_add_dialog(e):
        if dialog_add not in page.overlay:
            page.overlay.append(dialog_add)
        dialog_add.open = True
        page.update()

    def remove_exercise(ex_id):
        exercises_buffer[:] = [x for x in exercises_buffer if x.get('id') != ex_id]
        update_exercises_list()

    def update_exercises_list():
        exercises_column.controls.clear()
        for ex in exercises_buffer:
            if 'id' not in ex:
                ex['id'] = str(uuid.uuid4())[:8]
            nome = ex.get('exercise_name') or ex.get('name') or ex.get('nome') or '???'
            card = ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(nome, weight="bold", color="white", size=16),
                        ft.Text(f"{ex.get('serie','?')} x {ex.get('ripetizioni','?')}", color="#94a3b8", size=14)
                    ], expand=True),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="red",
                                  on_click=lambda e, x=ex.get('id'): remove_exercise(x))
                ]),
                bgcolor="#1e293b", border_radius=10, padding=15,
                border=ft.Border.all(1, "#334155")
            )
            exercises_column.controls.append(card)
        lbl_esercizi_count.value = f"ESERCIZI ({len(exercises_buffer)})"
        page.update()

    # --- SALVATAGGIO: OFF-CHAIN + ON-CHAIN ---
    def salva_scheda_logico(e):
        nome_scheda = txt_nome.controls[1].value.strip()
        split_type  = txt_split.controls[1].value.strip()

        if not nome_scheda:
            show_snack("Inserisci un nome per la scheda!", "orange")
            return

        if not exercises_buffer:
            show_snack("Aggiungi almeno un esercizio!", "orange")
            return

        # Verifica che il wallet sia configurato in sessione
        if not private_key:
            show_snack("Errore: nessuna chiave privata in sessione. Rifai il login.", "red")
            return

        dati_scheda = {
            "id": scheda_da_modificare.get("id", str(uuid.uuid4())) if is_editing else str(uuid.uuid4()),
            "type": "scheda",
            "user_address": user_address,
            "nome_scheda": nome_scheda,
            "split_type": split_type,
            "esercizi": exercises_buffer,
            "created_at": scheda_da_modificare.get("created_at", datetime.now().isoformat()) if is_editing else datetime.now().isoformat(),
        }

        # Feedback visivo
        btn_salva.disabled = True
        btn_salva.text = "Salvataggio..."
        page.update()

        try:
            # ---------------------------------------------------------------
            # STEP 1 — Salvataggio OFF-CHAIN (locale, GDPR compliant)
            # I dati completi vengono scritti su disco. Solo l'hash va on-chain.
            # ---------------------------------------------------------------
            save_workout_local(user_address, dati_scheda)

            # ---------------------------------------------------------------
            # STEP 2 — Salvataggio ON-CHAIN (solo l'hash SHA-256)
            # Lezione 3 + Lezione 5: la funzione firma e invia la transazione.
            # ---------------------------------------------------------------
            tx_hash = store_workout_on_chain(user_address, private_key, dati_scheda)

            page.session.store.set("scheda_edit", None)
            show_snack(f"✅ Scheda salvata! TX: {tx_hash[:18]}...", "green")
            page.go("/schede")

        except Exception as ex:
            print(f"Errore salvataggio scheda: {ex}")
            show_snack(f"❌ Errore Blockchain: {str(ex)}", "red")
            btn_salva.disabled = False
            btn_salva.text = "Salva"
            page.update()

    def go_back(e):
        page.session.store.set("scheda_edit", None)
        page.go("/schede")

    update_exercises_list()

    btn_salva = ft.ElevatedButton("Salva", bgcolor=ft.Colors.BLUE_500, color="white",
                                  on_click=salva_scheda_logico)

    page_title_text = "Modifica Scheda" if is_editing else "Nuova Scheda"

    return ft.View(
        route="/crea_scheda",
        bgcolor="#0f172a",
        padding=ft.Padding(top=60, left=20, right=20, bottom=20),
        controls=[
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK_IOS, icon_color="white", on_click=go_back, icon_size=18),
                ft.Text(page_title_text, size=20, weight="bold", color="white"),
                ft.Container(expand=True),
                btn_salva
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(color="transparent", height=10),
            ft.Column(
                controls=[
                    txt_nome, ft.Container(height=10),
                    txt_split, ft.Divider(color="transparent", height=20),
                    lbl_esercizi_count, ft.Container(height=5),
                    exercises_column, ft.Container(height=10),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.ADD, color=ft.Colors.BLUE_400),
                            ft.Text("Aggiungi Esercizio", color=ft.Colors.BLUE_400, weight="bold")
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        padding=15,
                        border=ft.Border.all(1, ft.Colors.BLUE_900),
                        border_radius=12,
                        on_click=open_add_dialog,
                        ink=True
                    ),
                    ft.Container(height=20)
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True
            )
        ],
        navigation_bar=ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.FOLDER_COPY, label="Schede"),
                ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
                ft.NavigationBarDestination(icon=ft.Icons.SPORTS_GYMNASTICS, label="Allenamento"),
            ],
            bgcolor="#1e293b", indicator_color=ft.Colors.BLUE_600,
            selected_index=0,
            on_change=lambda e: [
                page.session.store.set("scheda_edit", None),
                page.go("/schede") if e.control.selected_index == 0 else
                page.go("/") if e.control.selected_index == 1 else
                page.go("/workout")
            ]
        )
    )
