import flet as ft
import asyncio
from services.local_db import get_local_workouts as get_workout_logs
from services.blockchain_db import verifica_integrita_onchain

_cache_storico = None

def workout_view(page: ft.Page):
    global _cache_storico

    user_address = page.session.store.get("user_address")

    history_column  = ft.ListView(spacing=10, expand=True,
                                   padding=ft.Padding.only(left=0, top=0, right=10, bottom=100))
    loading_history = ft.ProgressRing(color=ft.Colors.CYAN_400)

    # --- NUOVA FUNZIONE: Navigazione al dettaglio ---
    def vai_a_dettaglio_allenamento(log_data):
        page.session.store.set("allenamento_selezionato", log_data)
        page.go("/dettaglio_allenamento")

    def render_logs(logs: list):
        history_column.controls.clear()
        only_logs = [l for l in logs if l.get("type") == "workout_log"]

        if not only_logs:
            history_column.controls.append(
                ft.Container(
                    content=ft.Text("Nessun allenamento registrato.", color="grey", italic=True),
                    padding=20
                )
            )
        else:
            for log in reversed(only_logs):
                nome   = log.get("nome_scheda", "Allenamento")
                data   = log.get("data", "Data sconosciuta")
                durata = log.get("durata", "--")
                n_ex   = len(log.get("dettagli_esercizi", []))

                lbl_verifica = ft.Text("", size=12, italic=True)

                def on_verifica(e, log_data=log, label=lbl_verifica):
                    label.value = "⏳ Verifica in corso..."
                    label.color = "grey"
                    page.update()
                    dati_per_hash = {k: v for k, v in log_data.items()
                                     if k != '_local_filename'}
                    esito, messaggio = verifica_integrita_onchain(user_address, dati_per_hash)
                    label.value = messaggio
                    label.color = ft.Colors.GREEN_400 if esito else ft.Colors.RED_400
                    page.update()

                card = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Column([
                                ft.Text(nome, weight="bold", color="white", size=16),
                                ft.Row([
                                    ft.Icon(ft.Icons.CALENDAR_TODAY, size=14, color="grey"),
                                    ft.Text(data, color="grey", size=13),
                                    ft.Container(width=10),
                                    ft.Icon(ft.Icons.TIMER, size=14, color="grey"),
                                    ft.Text(durata, color="grey", size=13),
                                    ft.Container(width=10),
                                    ft.Icon(ft.Icons.FITNESS_CENTER, size=14, color="grey"),
                                    ft.Text(f"{n_ex} esercizi", color="grey", size=13),
                                ])
                            ], expand=True),
                            ft.IconButton(
                                icon=ft.Icons.VERIFIED_OUTLINED,
                                icon_color=ft.Colors.CYAN_400,
                                tooltip="Verifica integrità sulla Blockchain",
                                on_click=on_verifica
                            )
                        ]),
                        lbl_verifica
                    ]),
                    bgcolor="#1e293b",
                    border_radius=12,
                    padding=15,
                    border=ft.Border.all(1, "#334155"),
                    # AGGIUNTO: Rendiamo la card cliccabile per andare ai dettagli
                    on_click=lambda e, log_data=log: vai_a_dettaglio_allenamento(log_data),
                    ink=True  # Effetto ripple al click
                )
                history_column.controls.append(card)

        loading_history.visible = False
        page.update()

    async def load_history_async():
        global _cache_storico
        
        loading_history.visible = True
        page.update()
        await asyncio.sleep(0.05) 

        try:
            logs = get_workout_logs(user_address) if user_address else []
            _cache_storico = logs if logs else []
            render_logs(_cache_storico)
        except Exception as ex:
            print(f"Errore caricamento storico: {ex}")
            loading_history.visible = False
            page.update()

    def start_workout(scheda):
        page.session.store.set("workout_active_scheda", scheda)
        bs_schede.open = False
        page.update()
        page.go("/live_workout")

    bs_schede_content = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=10)
    bs_schede = ft.BottomSheet(
        ft.Container(
            content=bs_schede_content,
            padding=20,
            bgcolor="#1e293b",
            border_radius=ft.BorderRadius(top_left=20, top_right=20, bottom_left=0, bottom_right=0),
            height=500
        )
    )

    def open_start_dialog(e):
        all_data = get_workout_logs(user_address) if user_address else []
        bs_schede_content.controls.clear()
        bs_schede_content.controls.append(
            ft.Container(content=ft.Text("Scegli la scheda", size=20, weight="bold", color="white"),
                         padding=ft.Padding(bottom=10))
        )
        valid_schede = {
            s["id"]: s for s in all_data
            if (s.get("type") == "scheda" or ("split_type" in s and "durata" not in s))
            and s.get("id")
        }
        if not valid_schede:
            bs_schede_content.controls.append(
                ft.Text("Nessuna scheda trovata. Creane una prima!", color="red")
            )
        else:
            for s in valid_schede.values():
                tile = ft.ListTile(
                    leading=ft.Icon(ft.Icons.FITNESS_CENTER, color=ft.Colors.CYAN_400),
                    title=ft.Text(s.get("nome_scheda", "Scheda"), color="white", weight="bold"),
                    subtitle=ft.Text(f"{len(s.get('esercizi', []))} Esercizi", color="grey"),
                    on_click=lambda e, x=s: start_workout(x),
                    bgcolor="#0f172a",
                )
                bs_schede_content.controls.append(tile)
        if bs_schede not in page.overlay:
            page.overlay.append(bs_schede)
        bs_schede.open = True
        page.update()

    def nav_change(e):
        index = e.control.selected_index
        if index == 0:   page.go("/schede")
        elif index == 1: page.go("/")

    view = ft.View(
        route="/workout",
        bgcolor="#0f172a",
        padding=ft.Padding(top=60, left=0, right=0, bottom=0),
        controls=[
            ft.Container(
                padding=20,
                expand=True,
                content=ft.Column([
                    ft.Text("Storico Allenamenti", size=28, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Divider(color="transparent", height=10),
                    ft.Row([loading_history], alignment=ft.MainAxisAlignment.CENTER),
                    history_column
                ], expand=True)
            )
        ],
        floating_action_button=ft.FloatingActionButton(
            bgcolor=ft.Colors.CYAN_600,
            content=ft.Row([ft.Icon(ft.Icons.PLAY_ARROW), ft.Text("INIZIA", weight="bold")],
                           alignment=ft.MainAxisAlignment.CENTER),
            width=120,
            on_click=open_start_dialog
        ),
        floating_action_button_location=ft.FloatingActionButtonLocation.CENTER_FLOAT,
        navigation_bar=ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.FOLDER_COPY, label="Schede"),
                ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
                ft.NavigationBarDestination(icon=ft.Icons.SPORTS_GYMNASTICS, label="Allenamento"),
            ],
            bgcolor="#1e293b",
            indicator_color=ft.Colors.BLUE_600,
            selected_index=2,
            on_change=nav_change
        )
    )

    page.run_task(load_history_async)
    return view