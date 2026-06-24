import flet as ft
import asyncio
from services.local_db import get_local_workouts as get_schede

_cache_schede = None

def schede_view(page: ft.Page):
    user_address = page.session.store.get("user_address") or "unknown_user"
    cards_column = ft.Column(spacing=10)

    loading_widget = ft.Row(
        [ft.ProgressRing(color=ft.Colors.CYAN_400)],
        alignment=ft.MainAxisAlignment.CENTER,
        visible=True
    )

    def andare_a_crea(e):
        page.session.store.set("scheda_edit", None)
        page.go("/crea_scheda")

    def vai_a_modifica(scheda_data):
        page.session.store.set("scheda_edit", scheda_data)
        page.go("/crea_scheda")

    def esegui_cancellazione(scheda_id):
        global _cache_schede
        _cache_schede = None
        page.run_task(refresh_data_async)

    # ------------------------------------------------------------------
    # RENDER
    # ------------------------------------------------------------------
    def render_schede(unique_schede: dict):
        cards_column.controls.clear()

        if not unique_schede:
            cards_column.controls.append(
                ft.Text("Nessuna scheda trovata. Creane una nuova!", color="grey", italic=True)
            )
        else:
            for s in unique_schede.values():
                titolo = s.get("nome_scheda", "Senza Titolo")
                split  = s.get("split_type", "General")
                num_ex = len(s.get("esercizi", []))

                card = ft.Container(
                    content=ft.ListTile(
                        title=ft.Text(titolo, color="white", weight="bold"),
                        subtitle=ft.Text(f"Focus: {split} | {num_ex} Esercizi", color="#94a3b8"),
                        on_click=lambda e, data=s: [
                            page.session.store.set("scheda_selezionata", data),
                            page.go("/dettaglio")
                        ],
                        trailing=ft.PopupMenuButton(
                            items=[
                                ft.PopupMenuItem(
                                    "Modifica", icon=ft.Icons.EDIT,
                                    on_click=lambda e, data=s: vai_a_modifica(data)
                                ),
                                ft.PopupMenuItem(
                                    "Elimina", icon=ft.Icons.DELETE,
                                    on_click=lambda e, sid=s.get("id"): esegui_cancellazione(sid)
                                ),
                            ]
                        )
                    ),
                    bgcolor="#1e293b",
                    border_radius=12,
                    padding=5
                )
                cards_column.controls.append(card)

        loading_widget.visible = False
        page.update()

    # ------------------------------------------------------------------
    # CARICAMENTO DATI — async con page.run_task()
    #
    # Il problema precedente: threading.Thread partiva prima che Flet
    # montasse la view in page.views, quindi page.update() veniva
    # ignorato silenziosamente e la rotella non spariva mai.
    #
    # La soluzione: page.run_task() schedula la coroutine nell'event loop
    # di Flet. L'await asyncio.sleep(0.05) cede il controllo per un
    # frame, garantendo che la view sia già registrata quando arriva
    # il primo page.update().
    # ------------------------------------------------------------------
    async def refresh_data_async():
        global _cache_schede
        
        # Rimuoviamo il blocco che usava la cache sempre:
        # Se vogliamo che sia reattivo, leggiamo dal disco ogni volta che carichiamo la vista.
        # Il file JSON è piccolo, non avrai problemi di performance.
        
        loading_widget.visible = True
        page.update()
        await asyncio.sleep(0.05) 

        try:
            tutti = get_schede(user_address)

            unique = {}
            for s in (tutti or []):
                # Mantieni il tuo filtro originale
                if s.get("type") == "scheda" or ("split_type" in s and "durata" not in s):
                    sid = s.get("id")
                    if sid:
                        unique[sid] = s

            _cache_schede = unique
            render_schede(unique)

        except Exception as ex:
            print(f"Errore caricamento schede: {ex}")
            loading_widget.visible = False
            page.update()

    actions_row = ft.Row([
        ft.ElevatedButton(
            "Nuova Scheda",
            icon=ft.Icons.ADD,
            bgcolor=ft.Colors.CYAN_600,
            color="white",
            on_click=andare_a_crea
        ),
        ft.OutlinedButton(
            "Esercizi",
            icon=ft.Icons.SETTINGS,
            on_click=lambda e: page.go("/esercizi")
        )
    ])

    view = ft.View(
        route="/schede",
        bgcolor="#0f172a",
        padding=ft.Padding(top=60, left=20, right=20, bottom=20),
        controls=[
            ft.Column([
                ft.Container(
                    content=ft.Text("Le tue Schede", size=30,
                                    weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    margin=ft.Margin(bottom=20)
                ),
                actions_row,
                ft.Divider(color="transparent", height=20),
            ], spacing=0),
            ft.Container(
                content=ft.Column(
                    controls=[loading_widget, cards_column, ft.Container(height=50)],
                    scroll=ft.ScrollMode.AUTO,
                ),
                expand=True
            )
        ],
        navigation_bar=ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.FOLDER_COPY, label="Schede"),
                ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
                ft.NavigationBarDestination(icon=ft.Icons.SPORTS_GYMNASTICS, label="Allenamento"),
            ],
            bgcolor="#1e293b",
            indicator_color=ft.Colors.CYAN_600,
            selected_index=0,
            on_change=lambda e: (
                page.go("/schede")  if e.control.selected_index == 0 else
                page.go("/")        if e.control.selected_index == 1 else
                page.go("/workout")
            )
        )
    )

    # Avvio DOPO aver costruito la view, così Flet può montarla prima
    # che arrivi il primo page.update() dalla coroutine
    page.run_task(refresh_data_async)

    return view